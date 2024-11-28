import csv
import math
import os
import sys
import threading
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional, Tuple

import sentistrength
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

import MLbackend.src.centrality_analysis as centrality
import MLbackend.src.graphql_analysis.graphql_analysis_helper as gql
import MLbackend.src.stats_analysis as stats
from MLbackend.src.configuration import Configuration
from MLbackend.src.perspective_analysis import getToxicityPercentage
from MLbackend.src.utils.result import Result


def pr_analysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
    result: Result,
) -> Tuple[List[List[List[str]]], List[List[str]]]:

    logger.info("Querying PRs")
    batches = prRequest(
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
        logger.info(f"Analyzing PR batch #{batch_idx}")

        # extract data from batch
        pr_count = len(batch)
        participants = list(
            pr["participants"] for pr in batch if len(pr["participants"]) > 0
        )
        batch_participants.append(participants)

        all_comments = list()
        pr_positive_comments = list()
        pr_negative_comments = list()
        generally_negative = list()

        semaphore = threading.Semaphore(15)
        threads = []
        for pr in batch:

            comments = list(
                comment for comment in pr["comments"] if comment and comment.strip()
            )

            # split comments that are longer than 20KB
            split_comments = []
            for comment in comments:

                # calc number of chunks
                byte_chunks = math.ceil(sys.getsizeof(comment) / (20 * 1024))
                if byte_chunks > 1:

                    # calc desired max length of each chunk
                    chunk_length = math.floor(len(comment) / byte_chunks)

                    # divide comment into chunks
                    chunks = [
                        comment[i * chunk_length : i * chunk_length + chunk_length]
                        for i in range(0, byte_chunks)
                    ]

                    # save chunks
                    split_comments.extend(chunks)

                else:
                    # append comment as-is
                    split_comments.append(comment)

            # re-assign comments after chunking
            comments = split_comments

            if len(comments) == 0:
                pr_positive_comments.append(0)
                pr_negative_comments.append(0)
                continue

            all_comments.extend(comments)

            thread = threading.Thread(
                target=analyze_sentiments,
                args=(
                    senti,
                    comments,
                    pr_positive_comments,
                    pr_negative_comments,
                    generally_negative,
                    semaphore,
                ),
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # save comments
        batch_comments.append(all_comments)

        # get comment length stats
        comment_lengths = [len(c) for c in all_comments]

        try:
            generally_negative_ratio = len(generally_negative) / pr_count
        except ZeroDivisionError:
            logger.warning(
                f"There are no PRs in batch #{batch_idx} so setting generally negative ratio as 0."
            )
            generally_negative_ratio = 0

        # get pr duration stats
        durations = [(pr["closedAt"] - pr["created_at"]).days for pr in batch]

        comment_sentiments = []
        comment_sentiments_positive = 0
        comment_sentiments_negative = 0

        if len(all_comments) > 0:
            comment_sentiments = senti.getSentiment(all_comments)
            comment_sentiments_positive = sum(
                1 for _ in filter(lambda value: value >= 1, comment_sentiments)
            )
            comment_sentiments_negative = sum(
                1 for _ in filter(lambda value: value <= -1, comment_sentiments)
            )

        toxicityPercentage = getToxicityPercentage(config, all_comments, logger)

        author, meta, metrics_data = centrality.buildGraphQlNetwork(batch_idx, participants, "PRs", config, logger, result)

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
            w.writerow(["PRCommentsToxicityPercentage", toxicityPercentage])

        meta1 = [
            ["Metric", "Value"],
            ["NumberPRs", pr_count],
            ["NumberPRComments", len(all_comments)],
            ["PRCommentsPositive", comment_sentiments_positive],
            ["PRCommentsNegative", comment_sentiments_negative],
            ["PRCommentsNegativeRatio", generally_negative_ratio],
            ["PRCommentsToxicityPercentage", toxicityPercentage],
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
        len_com = stats.outputStatistics(
            batch_idx,
            comment_lengths,
            "PRCommentsLength",
            config.resultsPath,
            logger,
        )

        pr_dur = stats.outputStatistics(
            batch_idx,
            durations,
            "PRDuration",
            config.resultsPath,
            logger,
        )

        pr_com_c = stats.outputStatistics(
            batch_idx,
            [len(pr["comments"]) for pr in batch],
            "PRCommentsCount",
            config.resultsPath,
            logger,
        )

        pr_com = stats.outputStatistics(
            batch_idx,
            [pr["commit_count"] for pr in batch],
            "PRCommitsCount",
            config.resultsPath,
            logger,
        )

        pr_com_sent = stats.outputStatistics(
            batch_idx,
            comment_sentiments,
            "PRCommentSentiments",
            config.resultsPath,
            logger,
        )

        pr_part = stats.outputStatistics(
            batch_idx,
            [len(set(pr["participants"])) for pr in batch],
            "PRParticipantsCount",
            config.resultsPath,
            logger,
        )

        pr_pos = stats.outputStatistics(
            batch_idx,
            pr_positive_comments,
            "PRCountPositiveComments",
            config.resultsPath,
            logger,
        )

        pr_neg = stats.outputStatistics(
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


def analyze_sentiments(
    senti, comments, positive_comments, negative_comments, generally_negative, semaphore
):
    with semaphore:
        comment_sentiments = (
            senti.getSentiment(comments, score="scale")
            if len(comments) > 1
            else senti.getSentiment(comments[0])
        )

        comment_sentiments_positive = sum(
            1 for _ in filter(lambda value: value >= 1, comment_sentiments)
        )
        comment_sentiments_negative = sum(
            1 for _ in filter(lambda value: value <= -1, comment_sentiments)
        )

        lock = threading.Lock()
        with lock:
            positive_comments.append(comment_sentiments_positive)
            negative_comments.append(comment_sentiments_negative)

            if comment_sentiments_negative / len(comments) > 0.5:
                generally_negative.append(True)


def prRequest(
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
        result = gql.runGraphqlRequest(pat, query, logger)

        # Get all the nodes in the result
        try:
            nodes = result["repository"]["pullRequests"]["nodes"]
        except TypeError:
            # There are no PRs in this repository
            logger.error("There are no PRs for this repository")
            break

        # Add all nodes that are required
        for node in nodes:
            created_at = isoparse(node["created_at"])
            closed_at = (
                current_time if node["closedAt"] is None else isoparse(node["closedAt"])
            )

            authors: List[str] = list()
            for user_node in node["participants"]["nodes"]:
                gql.add_login(node=user_node, authors=authors)

            pr: Dict[str, Any] = {
                "number": node["number"],
                "created_at": created_at,
                "closedAt": closed_at,
                "comments": [
                    comment["bodyText"] for comment in node["comments"]["nodes"]
                ],
                "commit_count": node["commits"]["totalCount"],
                "participants": authors,
            }

            batch_date: Optional[datetime] = None

            for date in batches_pre.keys():
                batch_date = date
                if date <= created_at < date + delta:
                    # This means we have exceeded the range by 1
                    break

            if batch_date is not None:
                batches_pre[batch_date].append(pr)
            else:
                if current_time not in batches_pre.keys():
                    batches_pre[current_time] = []
                batches_pre[current_time].append(pr)

        # check for next page
        page_info = result["repository"]["pullRequests"]["page_info"]
        if not page_info["hasNextPage"]:
            # There is no next page to query
            no_next_page = True
        else:
            cursor = page_info["endCursor"]
            query = build_pr_request_query(owner=owner, name=name, cursor=cursor)

    return list(batches_pre.values())


def build_pr_request_query(owner: str, name: str, cursor: str):
    return """{{
        repository(owner: "{0}", name: "{1}") {{
            pullRequests(first:100{2}) {{
                page_info {{
                    endCursor
                    hasNextPage
                }}
                nodes {{
                    number
                    created_at
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
