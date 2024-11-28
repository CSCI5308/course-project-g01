import csv
import os
from collections import Counter
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List

import networkx as nx
from dateutil.relativedelta import relativedelta
from git.objects import Commit
from networkx.algorithms.community import greedy_modularity_communities

from MLbackend.src.configuration import Configuration
from MLbackend.src.stats_analysis import outputStatistics
from MLbackend.src.utils import author_id_extractor
from MLbackend.src.utils.result import Result


def centralityAnalysis(
    commits: List[Commit],
    delta: relativedelta,
    batch_dates: List[datetime],
    config: Configuration,
    logger: Logger,
    result:Result,
) -> List[List[Any]]:
    coreDevs: List[List[Any]] = list()

    # work with batched commits
    central_meta = []
    central_metric = []

    for idx, batch_start_date in enumerate(batch_dates):
        batch_end_date = batch_start_date + delta

        batch = [
            commit
            for commit in commits
            if commit.committed_datetime >= batch_start_date
            and commit.committed_datetime < batch_end_date
        ]

        batch_core_devs, cen_meta, cen_metric = processBatch(idx, batch, config,logger,result)
        central_meta.append(cen_meta)
        central_metric.append(cen_metric)
        coreDevs.append(batch_core_devs)

    return coreDevs, central_meta[0], central_metric[0]


def processBatch(
    batch_idx: int, commits: List[Commit], config: Configuration, logger: Logger, result: Result
) -> List[Any]:
    all_related_authors = {}
    authorCommits = Counter({})

    # for all commits...
    logger.info("Analyzing centrality for commits")
    for commit in commits:
        author = author_id_extractor(commit.author)

        # increase author commit count
        authorCommits.update({author: 1})

        # initialize dates for related author analysis
        commit_date = datetime.fromtimestamp(commit.committed_date)
        earliest_date = commit_date + relativedelta(months=-1)
        latest_date = commit_date + relativedelta(months=+1)

        commitRelatedCommits = filter(
            lambda c: find_related_commits(author, earliest_date, latest_date, c), commits
        )

        commitRelatedAuthors = set(
            list(map(lambda c: author_id_extractor(c.author), commitRelatedCommits))
        )

        # get current related authors collection and update it
        author_related_authors = all_related_authors.setdefault(author, set())
        author_related_authors.update(commitRelatedAuthors)

    return prepare_graph(
        all_related_authors, authorCommits, batch_idx, "commitCentrality", config, logger, result
    )


def buildGraphQlNetwork(
    batch_idx: int, batch: list, prefix: str, config: Configuration, logger: Logger, result: Result
):
    all_related_authors = {}
    author_items = Counter({})

    # for all commits...
    logger.info("Analyzing centrality")
    for authors in batch:

        for author in authors:

            # increase author commit count
            author_items.update({author: 1})

            # get current related authors collection and update it
            related_authors = set(
                related_author
                for otherAuthors in batch
                for related_author in otherAuthors
                if author in otherAuthors and related_author != author
            )
            author_related_authors = all_related_authors.setdefault(author, set())
            author_related_authors.update(related_authors)
    return prepare_graph(all_related_authors, author_items, batch_idx, prefix, config, logger, result)


def prepare_graph(
    all_related_authors: dict,
    author_items: Counter,
    batch_idx: int,
    output_prefix: str,
    config: Configuration,
    logger: Logger,
    result: Result,
) -> List[Any]:

    # prepare graph
    logger.info(f"Preparing NX graph for {output_prefix}")
    G = nx.Graph()

    for author in all_related_authors:
        G.add_node(author)

        for related_author in all_related_authors[author]:
            G.add_edge(author.strip(), related_author.strip())

    # analyze graph
    closeness = dict(nx.closeness_centrality(G))
    betweenness = dict(nx.betweenness_centrality(G))
    centrality: Dict[Any, float] = dict(nx.degree_centrality(G))
    density = nx.density(G)
    modularity = []

    try:
        for idx, community in enumerate(greedy_modularity_communities(G)):
            author_count = len(community)
            community_commit_count = sum(author_items[author] for author in community)
            row = [author_count, community_commit_count]
            modularity.append(row)
    except ZeroDivisionError:
        # not handled
        logger.warning(
            f"A zero division error occured while preparing graph for {output_prefix}."
        )
        pass

    # finding high centrality authors
    highCentralityAuthors: List[Any] = [
        author
        for author, centrality_value in centrality.items()
        if centrality_value > 0.5
    ]
    if result:
        for author in highCentralityAuthors:
            result.addCoreDev(author)

    number_high_centrality_authors = len(highCentralityAuthors)

    try:
        percentage_high_centrality_authors = number_high_centrality_authors / len(
            all_related_authors
        )
    except ZeroDivisionError:
        percentage_high_centrality_authors = 0
        logger.warning(
            f"Length of related authors is 0 while computing percentage of high centrality authors in {output_prefix}"
        )

    # calculate TFN
    tfn = len(author_items) - number_high_centrality_authors

    # calculate TFC
    try:
        tfc = (
            sum(author_items[author] for author in highCentralityAuthors)
            / sum(author_items.values())
            * 100
        )
    except ZeroDivisionError:
        tfc = 0
        logger.warning(
            f"Sum of author values is 0 while computing TFC in {output_prefix}"
        )

    logger.info(f"Outputting CSVs for {output_prefix}")

    # output non-tabular results
    with open(
        os.path.join(config.resultsPath, f"results_{batch_idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow([f"{output_prefix}_Density", density])
        w.writerow([f"{output_prefix}_Community Count", len(modularity)])
        w.writerow([f"{output_prefix}_TFN", tfn])
        w.writerow([f"{output_prefix}_TFC", tfc])
    results_meta = [
        ["Metric", "Value"],
        [f"{output_prefix}_Density", density],
        [f"{output_prefix}_Community Count", len(modularity)],
        [f"{output_prefix}_TFN", tfn],
        [f"{output_prefix}_TFC", tfc],
    ]

    # output community information
    with open(
        os.path.join(config.metricsPath, f"{output_prefix}_community_{batch_idx}.csv"),
        "a",
        newline="",
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Community Index", "Author Count", "Item Count"])
        for idx, community in enumerate(modularity):
            w.writerow([idx + 1, community[0], community[1]])

    # combine centrality results
    combined = {}
    for key in closeness:
        single = {
            "Author": key,
            "Closeness": closeness[key],
            "Betweenness": betweenness[key],
            "Centrality": centrality[key],
        }

        combined[key] = single

    # output tabular results
    with open(
        os.path.join(config.metricsPath, f"{output_prefix}_centrality_{batch_idx}.csv"),
        "w",
        newline="",
    ) as f:
        w = csv.DictWriter(f, ["Author", "Closeness", "Betweenness", "Centrality"])
        w.writeheader()

        for key in combined:
            w.writerow(combined[key])

    # output high centrality authors
    with open(
        os.path.join(config.resultsPath, f"results_{batch_idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(
            [f"{output_prefix}_NumberHighCentralityAuthors", number_high_centrality_authors]
        )
        w.writerow(
            [
                f"{output_prefix}_PercentageHighCentralityAuthors",
                percentage_high_centrality_authors,
            ]
        )

    results_meta.append(
        [f"{output_prefix}_NumberHighCentralityAuthors", number_high_centrality_authors]
    )
    results_meta.append(
        [
            f"{output_prefix}_PercentageHighCentralityAuthors",
            percentage_high_centrality_authors,
        ]
    )

    # output statistics
    close = outputStatistics(
        batch_idx,
        [value for key, value in closeness.items()],
        f"{output_prefix}_Closeness",
        config.resultsPath,
        logger,
    )

    between = outputStatistics(
        batch_idx,
        [value for key, value in betweenness.items()],
        f"{output_prefix}_Betweenness",
        config.resultsPath,
        logger,
    )

    central = outputStatistics(
        batch_idx,
        [value for key, value in centrality.items()],
        f"{output_prefix}_Centrality",
        config.resultsPath,
        logger,
    )

    author_c = outputStatistics(
        batch_idx,
        [community[0] for community in modularity],
        f"{output_prefix}_CommunityAuthorCount",
        config.resultsPath,
        logger,
    )

    author_item = outputStatistics(
        batch_idx,
        [community[1] for community in modularity],
        f"{output_prefix}_CommunityAuthorItemCount",
        config.resultsPath,
        logger,
    )

    metrics_data = [("Metric", "Count", "Mean", "Stdev")]
    metrics_data.extend([close, between, central, author_c, author_item])

    nx.write_graphml(
        G, os.path.join(config.resultsPath, f"{output_prefix}_{batch_idx}.xml")
    )

    return highCentralityAuthors, results_meta, metrics_data


# helper functions
def find_related_commits(author, earliest_date, latest_date, commit):
    is_different_author = author != author_id_extractor(commit.author)
    if not is_different_author:
        return False

    commit_date = datetime.fromtimestamp(commit.committed_date)
    is_in_range = commit_date >= earliest_date and commit_date <= latest_date
    return is_in_range
