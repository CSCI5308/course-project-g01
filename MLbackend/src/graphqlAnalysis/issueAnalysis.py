import csv
import math
import os
import sys
import threading
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional

import sentistrength
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

import MLbackend.src.centralityAnalysis as centrality
import MLbackend.src.graphqlAnalysis.graphqlAnalysisHelper as gql
import MLbackend.src.statsAnalysis as stats
from MLbackend.src.configuration import Configuration
from MLbackend.src.perspectiveAnalysis import getToxicityPercentage
from MLbackend.src.utils.result import Result

def issueAnalysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger, 
    result:Result   

):

    logger.info("Querying issue comments")
    batches = issueRequest(
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
        logger.info(f"Analyzing issue batch #{batch_idx}")

        # extract data from batch
        issueCount = len(batch)
        participants = list(
            issue["participants"] for issue in batch if len(issue["participants"]) > 0
        )
        batch_participants.append(participants)

        all_comments = list()
        issuePositiveComments = list()
        issueNegativeComments = list()
        generally_negative = list()

        semaphore = threading.Semaphore(15)
        threads = []
        for issue in batch:
            comments = list(
                comment for comment in issue["comments"] if comment and comment.strip()
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
                issuePositiveComments.append(0)
                issueNegativeComments.append(0)
                continue

            all_comments.extend(comments)

            thread = threading.Thread(
                target=analyzeSentiments,
                args=(
                    senti,
                    comments,
                    issuePositiveComments,
                    issueNegativeComments,
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
            generally_negative_ratio = len(generally_negative) / issueCount
        except ZeroDivisionError:
            generally_negative_ratio = 0
            logger.warning(
                f"There are no Issues for batch #{batch_idx} setting generally negative ratio as 0."
            )

        # get pr duration stats
        durations = [(pr["closedAt"] - pr["created_at"]).days for pr in batch]

        # analyze comment issue sentiment
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

        author, meta, metrics_data = centrality.buildGraphQlNetwork(batch_idx, participants, "Issues", config, logger,result)

        logger.info("Writing GraphQL analysis results")
        with open(
            os.path.join(config.resultsPath, f"results_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["NumberIssues", len(batch)])
            w.writerow(["NumberIssueComments", len(all_comments)])
            w.writerow(["IssueCommentsPositive", comment_sentiments_positive])
            w.writerow(["IssueCommentsNegative", comment_sentiments_negative])
            w.writerow(["IssueCommentsNegativeRatio", generally_negative_ratio])
            w.writerow(["IssueCommentsToxicityPercentage", toxicityPercentage])

        meta1 = [
            ["Metrics", "Issue"],
            ["NumberIssues", len(batch)],
            ["NumberIssueComments", len(all_comments)],
            ["IssueCommentsPositive", comment_sentiments_positive],
            ["IssueCommentsNegative", comment_sentiments_negative],
            ["IssueCommentsNegativeRatio", generally_negative_ratio],
            ["IssueCommentsToxicityPercentage", toxicityPercentage],
        ]

        with open(
            os.path.join(config.metricsPath, f"issueCommentsCount_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Issue Number", "Comment Count"])
            for issue in batch:
                w.writerow([issue["number"], len(issue["comments"])])

        with open(
            os.path.join(config.metricsPath, f"issueParticipantCount_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Issue Number", "Developer Count"])
            for issue in batch:
                w.writerow([issue["number"], len(set(issue["participants"]))])

        # output statistics
        issue_len = stats.outputStatistics(
            batch_idx,
            comment_lengths,
            "IssueCommentsLength",
            config.resultsPath,
            logger,
        )

        issue_dur = stats.outputStatistics(
            batch_idx,
            durations,
            "IssueDuration",
            config.resultsPath,
            logger,
        )

        issue_com = stats.outputStatistics(
            batch_idx,
            [len(issue["comments"]) for issue in batch],
            "IssueCommentsCount",
            config.resultsPath,
            logger,
        )

        sent = stats.outputStatistics(
            batch_idx,
            comment_sentiments,
            "IssueCommentSentiments",
            config.resultsPath,
            logger,
        )

        part = stats.outputStatistics(
            batch_idx,
            [len(set(issue["participants"])) for issue in batch],
            "IssueParticipantCount",
            config.resultsPath,
            logger,
        )

        pos = stats.outputStatistics(
            batch_idx,
            issuePositiveComments,
            "IssueCountPositiveComments",
            config.resultsPath,
            logger,
        )

        neg = stats.outputStatistics(
            batch_idx,
            issueNegativeComments,
            "IssueCountNegativeComments",
            config.resultsPath,
            logger,
        )
        metrics_data1 = [("Metric", "Count", "Mean", "Stdev")]
        metrics_data1.extend([issue_len, issue_dur, issue_com, sent, part, pos, neg])
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


def analyzeSentiments(
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


def issueRequest(
    pat: str,
    owner: str,
    name: str,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
) -> None:

    query = buildIssueRequestQuery(owner=owner, name=name, cursor=None)

    batches_pre: Dict[datetime, List[Dict[str, Any]]] = {
        date: [] for date in batch_dates
    }
    current_time: datetime = datetime.now(batch_dates[-1].tzinfo)

    no_next_page: bool = False

    while not no_next_page:

        # Get chunk of page
        result = gql.runGraphqlRequest(pat=pat, query=query, logger=logger)

        # Get all the nodes in the result
        try:
            nodes = result["repository"]["issues"]["nodes"]
        except TypeError:
            # There are no PRs in this repository
            logger.error("There are no Issues for this repository")
            break

        # Add all nodes that are required
        for node in nodes:

            created_at: datetime = isoparse(node["created_at"])
            closed_at: datetime = (
                current_time if node["closedAt"] is None else isoparse(node["closedAt"])
            )

            # Get all the authors
            authors: List[str] = list()
            for user_node in node["participants"]["nodes"]:
                gql.addLogin(node=user_node, authors=authors)

            # Create the issue dictionary
            issue: Dict[str, Any] = {
                "number": node["number"],
                "created_at": created_at,
                "closedAt": closed_at,
                "comments": [
                    comment["bodyText"] for comment in node["comments"]["nodes"]
                ],
                "participants": authors,
            }

            batch_date: Optional[datetime] = None

            for date in batches_pre.keys():
                batch_date = date
                if date <= created_at < date + delta:
                    # This means we have exceeded the range by 1
                    break

            if batch_date is not None:
                batches_pre[batch_date].append(issue)
            else:
                if current_time not in batches_pre.keys():
                    batches_pre[current_time] = []
                batches_pre[current_time].append(issue)

        # Check for next page
        page_info = result["repository"]["issues"]["page_info"]
        if not page_info["hasNextPage"]:
            no_next_page = True
        else:
            cursor = page_info["endCursor"]
            query = buildIssueRequestQuery(owner=owner, name=name, cursor=cursor)

    return list(batches_pre.values())


def buildIssueRequestQuery(owner: str, name: str, cursor: str):
    return """{{
        repository(owner: "{0}", name: "{1}") {{
            issues(first: 100{2}) {{
                page_info {{
                    hasNextPage
                    endCursor
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
                    comments(first: 100) {{
                        nodes {{
                            bodyText
                        }}
                    }}
                }}
            }}
        }}
    }}""".format(
        owner, name, gql.buildNextPageQuery(cursor)
    )
