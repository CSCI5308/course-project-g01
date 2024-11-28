import csv
import os
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional

import sentistrength
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

import MLbackend.src.centrality_analysis as centrality
import MLbackend.src.graphql_analysis.graphql_analysis_helper as gql
import MLbackend.src.stats_analysis as stats
from MLbackend.src.configuration import Configuration
from MLbackend.src.utils import get_stats, get_comment_stats, create_analysis_batches
from MLbackend.src.utils.result import Result


def pr_analysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
    result: Result,
) -> tuple[
    list[Any], list[Any], Any, Any, list[list[str] | list[str | Any] | list[str | int] | list[str | float | int | Any]],
    list[tuple[str, str, str, str] | Any]]:

    logger.info("Querying PRs")
    batches = pr_request(
        config.pat,
        config.repositoryOwner,
        config.repositoryName,
        delta,
        batch_dates,
        logger,
    )

    batch_participants = list()
    batch_comments = list()
    results_meta = []
    results_metrics = []
    results_meta1 = []
    results_metrics1 = []

    for batch_idx, batch in enumerate(batches):
        generally_negative, pr_count, all_comments, participants, comment_lengths, pr_positive_comments, pr_negative_comments = get_stats(
            stat_type="PR", logger=logger, batch_idx=batch_idx, batch_participants=batch_participants, senti=senti, batch_comments=batch_comments, batch=batch)

        try:
            generally_negative_ratio = len(generally_negative) / pr_count
        except ZeroDivisionError:
            logger.warning(
                f"There are no PRs in batch #{batch_idx} so setting generally negative ratio as 0."
            )
            generally_negative_ratio = 0

        # get pr duration stats
        durations, comment_sentiments, comment_sentiments_positive, comment_sentiments_negative, toxicity_percentage = get_comment_stats(all_comments=all_comments, senti=senti, config=config, logger=logger, batch=batch)

        author, meta, metrics_data = centrality.build_grapql_network(batch_idx, participants, "PRs", config, logger, result)

        logger.info("Writing results of PR analysis to CSVs.")
        with open(
            os.path.join(config.resultsPath, f"results_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["NumberPRs", pr_count])
            w.writerow(["NumberPRComments", len(all_comments)])
            w.writerow(["PRCommentsPositive", comment_sentiments_positive])
            w.writerow(["PRCommentsNegative", comment_sentiments_negative])
            w.writerow(["PRCommentsNegativeRatio", generally_negative_ratio])
            w.writerow(["PRCommentsToxicityPercentage", toxicity_percentage])

        meta1 = [
            ["Metric", "Value"],
            ["NumberPRs", pr_count],
            ["NumberPRComments", len(all_comments)],
            ["PRCommentsPositive", comment_sentiments_positive],
            ["PRCommentsNegative", comment_sentiments_negative],
            ["PRCommentsNegativeRatio", generally_negative_ratio],
            ["PRCommentsToxicityPercentage", toxicity_percentage],
        ]

        with open(
            os.path.join(config.metricsPath, f"PRCommits_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["PR Number", "Commit Count"])
            for pr in batch:
                w.writerow([pr["number"], pr["commit_count"]])

        with open(
            os.path.join(config.metricsPath, f"PRParticipants_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["PR Number", "Developer Count"])
            for pr in batch:
                w.writerow([pr["number"], len(set(pr["participants"]))])

        # output statistics
        len_com = stats.output_statistics(
            batch_idx,
            comment_lengths,
            "PRCommentsLength",
            config.resultsPath,
            logger,
        )

        pr_dur = stats.output_statistics(
            batch_idx,
            durations,
            "PRDuration",
            config.resultsPath,
            logger,
        )

        pr_com_c = stats.output_statistics(
            batch_idx,
            [len(pr["comments"]) for pr in batch],
            "PRCommentsCount",
            config.resultsPath,
            logger,
        )

        pr_com = stats.output_statistics(
            batch_idx,
            [pr["commit_count"] for pr in batch],
            "PRCommitsCount",
            config.resultsPath,
            logger,
        )

        pr_com_sent = stats.output_statistics(
            batch_idx,
            comment_sentiments,
            "PRCommentSentiments",
            config.resultsPath,
            logger,
        )

        pr_part = stats.output_statistics(
            batch_idx,
            [len(set(pr["participants"])) for pr in batch],
            "PRParticipantsCount",
            config.resultsPath,
            logger,
        )

        pr_pos = stats.output_statistics(
            batch_idx,
            pr_positive_comments,
            "PRCountPositiveComments",
            config.resultsPath,
            logger,
        )

        pr_neg = stats.output_statistics(
            batch_idx,
            pr_negative_comments,
            "PRCountNegativeComments",
            config.resultsPath,
            logger,
        )

        metrics_data1 = [("Metric", "Count", "Mean", "Stdev")]
        metrics_data1.extend(
            [len_com, pr_dur, pr_com_c, pr_com, pr_com_sent, pr_part, pr_pos, pr_neg]
        )

        results_meta.append(meta)
        results_meta1.append(meta1)
        results_metrics.append(metrics_data)
        results_metrics1.append(metrics_data1)

    return (
        batch_participants,
        batch_comments,
        results_meta[0],
        results_metrics[0],
        results_meta1[0],
        results_metrics1[0],
    )


def pr_request(
    pat: str,
    owner: str,
    name: str,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
) -> List[List[Dict[str, Any]]]:

    query = build_pr_request_query(owner=owner, name=name, cursor=None)

    # prepare batches
    batches_pre: Dict[datetime, List[Dict[str, Any]]] = {
        date: [] for date in batch_dates
    }
    current_time: datetime = datetime.now(batch_dates[-1].tzinfo)
    no_next_page: bool = False

    while not no_next_page:

        # Get a chunk of page
        result = gql.run_graphql_request(pat, query, logger)

        # Get all the nodes in the result
        try:
            nodes = result["repository"]["pullRequests"]["nodes"]
        except TypeError:
            # There are no PRs in this repository
            logger.error("There are no PRs for this repository")
            break

        # Add all nodes that are required
        for node in nodes:
            created_at = isoparse(node["createdAt"])
            closed_at = (
                current_time if node["closedAt"] is None else isoparse(node["closedAt"])
            )

            authors: List[str] = list()
            for user_node in node["participants"]["nodes"]:
                gql.add_login(node=user_node, authors=authors)

            pr: Dict[str, Any] = {
                "number": node["number"],
                "created_at": created_at,
                "closed_at": closed_at,
                "comments": [
                    comment["bodyText"] for comment in node["comments"]["nodes"]
                ],
                "commit_count": node["commits"]["totalCount"],
                "participants": authors,
            }

            batches_pre = create_analysis_batches(batches_pre=batches_pre, created_at=created_at, delta=delta, entity=pr, current_time=current_time)

        # check for next page
        page_info = result["repository"]["pullRequests"]["pageInfo"]
        if not page_info["hasNextPage"]:
            # There is no next page to query
            no_next_page = True
        else:
            cursor = page_info["endCursor"]
            query = build_pr_request_query(owner=owner, name=name, cursor=cursor)

    return list(batches_pre.values())


def build_pr_request_query(owner: str, name: str, cursor: str | None):
    return """{{
        repository(owner: "{0}", name: "{1}") {{
            pullRequests(first:100{2}) {{
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
                nodes {{
                    number
                    createdAt
                    closedAt
                    participants(first: 100) {{
                        nodes {{
                            login
                        }}
                    }}
                    commits {{
                        totalCount
                    }}
                    comments(first: 100) {{
                        nodes {{
                            bodyText
                        }}
                    }}
                }}
            }}
        }}
    }}
    """.format(
        owner, name, gql.build_next_page_query(cursor)
    )
