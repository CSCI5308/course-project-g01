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

import MLbackend.src.centralityAnalysis as centrality
import MLbackend.src.graphqlAnalysis.graphqlAnalysisHelper as gql
import MLbackend.src.statsAnalysis as stats
from MLbackend.src.configuration import Configuration
from MLbackend.src.perspectiveAnalysis import getToxicityPercentage


def prAnalysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batchDates: List[datetime],
    logger: Logger,
) -> Tuple[List[List[List[str]]], List[List[str]]]:

    logger.info("Querying PRs")
    batches = prRequest(
        config.pat,
        config.repositoryOwner,
        config.repositoryName,
        delta,
        batchDates,
        logger,
    )

    batchParticipants = list()
    batchComments = list()
    results_meta = []
    results_metrics = []
    results_meta1 = []
    results_metrics1 = []


    for batchIdx, batch in enumerate(batches):
        logger.info(f"Analyzing PR batch #{batchIdx}")

        # extract data from batch
        prCount = len(batch)
        participants = list(
            pr["participants"] for pr in batch if len(pr["participants"]) > 0
        )
        batchParticipants.append(participants)

        allComments = list()
        prPositiveComments = list()
        prNegativeComments = list()
        generallyNegative = list()

        semaphore = threading.Semaphore(15)
        threads = []
        for pr in batch:

            comments = list(
                comment for comment in pr["comments"] if comment and comment.strip()
            )

            # split comments that are longer than 20KB
            splitComments = []
            for comment in comments:

                # calc number of chunks
                byteChunks = math.ceil(sys.getsizeof(comment) / (20 * 1024))
                if byteChunks > 1:

                    # calc desired max length of each chunk
                    chunkLength = math.floor(len(comment) / byteChunks)

                    # divide comment into chunks
                    chunks = [
                        comment[i * chunkLength : i * chunkLength + chunkLength]
                        for i in range(0, byteChunks)
                    ]

                    # save chunks
                    splitComments.extend(chunks)

                else:
                    # append comment as-is
                    splitComments.append(comment)

            # re-assign comments after chunking
            comments = splitComments

            if len(comments) == 0:
                prPositiveComments.append(0)
                prNegativeComments.append(0)
                continue

            allComments.extend(comments)

            thread = threading.Thread(
                target=analyzeSentiments,
                args=(
                    senti,
                    comments,
                    prPositiveComments,
                    prNegativeComments,
                    generallyNegative,
                    semaphore,
                ),
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # save comments
        batchComments.append(allComments)

        # get comment length stats
        commentLengths = [len(c) for c in allComments]

        try:
            generallyNegativeRatio = len(generallyNegative) / prCount
        except ZeroDivisionError:
            logger.warning(
                f"There are no PRs in batch #{batchIdx} so setting generally negative ratio as 0."
            )
            generallyNegativeRatio = 0

        # get pr duration stats
        durations = [(pr["closedAt"] - pr["createdAt"]).days for pr in batch]

        commentSentiments = []
        commentSentimentsPositive = 0
        commentSentimentsNegative = 0

        if len(allComments) > 0:
            commentSentiments = senti.getSentiment(allComments)
            commentSentimentsPositive = sum(
                1 for _ in filter(lambda value: value >= 1, commentSentiments)
            )
            commentSentimentsNegative = sum(
                1 for _ in filter(lambda value: value <= -1, commentSentiments)
            )

        toxicityPercentage = getToxicityPercentage(config, allComments, logger)

        author, meta, metrics_data = centrality.buildGraphQlNetwork(batchIdx, participants, "PRs", config, logger)

        logger.info("Writing results of PR analysis to CSVs.")
        with open(
            os.path.join(config.resultsPath, f"results_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["NumberPRs", prCount])
            w.writerow(["NumberPRComments", len(allComments)])
            w.writerow(["PRCommentsPositive", commentSentimentsPositive])
            w.writerow(["PRCommentsNegative", commentSentimentsNegative])
            w.writerow(["PRCommentsNegativeRatio", generallyNegativeRatio])
            w.writerow(["PRCommentsToxicityPercentage", toxicityPercentage])
        
        meta1 = [["Metric","Value"],["NumberPRs", prCount],["NumberPRComments", len(allComments)],
                 ["PRCommentsPositive", commentSentimentsPositive],["PRCommentsNegative", commentSentimentsNegative],
                 ["PRCommentsNegativeRatio", generallyNegativeRatio],["PRCommentsToxicityPercentage", toxicityPercentage]]


        with open(
            os.path.join(config.metricsPath, f"PRCommits_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["PR Number", "Commit Count"])
            for pr in batch:
                w.writerow([pr["number"], pr["commitCount"]])

        with open(
            os.path.join(config.metricsPath, f"PRParticipants_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["PR Number", "Developer Count"])
            for pr in batch:
                w.writerow([pr["number"], len(set(pr["participants"]))])

        # output statistics
        len_com = stats.outputStatistics(
            batchIdx,
            commentLengths,
            "PRCommentsLength",
            config.resultsPath,
            logger,

        )

        pr_dur = stats.outputStatistics(
            batchIdx,
            durations,
            "PRDuration",
            config.resultsPath,
            logger,
        )

        pr_com_c = stats.outputStatistics(
            batchIdx,
            [len(pr["comments"]) for pr in batch],
            "PRCommentsCount",
            config.resultsPath,
            logger,
        )

        pr_com = stats.outputStatistics(
            batchIdx,
            [pr["commitCount"] for pr in batch],
            "PRCommitsCount",
            config.resultsPath,
            logger,
        )

        pr_com_sent = stats.outputStatistics(
            batchIdx,
            commentSentiments,
            "PRCommentSentiments",
            config.resultsPath,
            logger,
        )

        pr_part = stats.outputStatistics(
            batchIdx,
            [len(set(pr["participants"])) for pr in batch],
            "PRParticipantsCount",
            config.resultsPath,
            logger,
        )

        pr_pos = stats.outputStatistics(
            batchIdx,
            prPositiveComments,
            "PRCountPositiveComments",
            config.resultsPath,
            logger,
        )

        pr_neg = stats.outputStatistics(
            batchIdx,
            prNegativeComments,
            "PRCountNegativeComments",
            config.resultsPath,
            logger,
        )

        metrics_data1 = [("Metric", "Count", "Mean", "Stdev")]
        metrics_data1.extend([
        len_com,
        pr_dur,
        pr_com_c,
        pr_com,
        pr_com_sent,
        pr_part,
        pr_pos,
        pr_neg])

        results_meta.append(meta)
        results_meta1.append(meta1)
        results_metrics.append(metrics_data)
        results_metrics1.append(metrics_data1)


    return batchParticipants, batchComments, results_meta[0], results_metrics[0], results_meta1[0], results_metrics1[0]


def analyzeSentiments(
    senti, comments, positiveComments, negativeComments, generallyNegative, semaphore
):
    with semaphore:
        commentSentiments = (
            senti.getSentiment(comments, score="scale")
            if len(comments) > 1
            else senti.getSentiment(comments[0])
        )

        commentSentimentsPositive = sum(
            1 for _ in filter(lambda value: value >= 1, commentSentiments)
        )
        commentSentimentsNegative = sum(
            1 for _ in filter(lambda value: value <= -1, commentSentiments)
        )

        lock = threading.Lock()
        with lock:
            positiveComments.append(commentSentimentsPositive)
            negativeComments.append(commentSentimentsNegative)

            if commentSentimentsNegative / len(comments) > 0.5:
                generallyNegative.append(True)


def prRequest(
    pat: str,
    owner: str,
    name: str,
    delta: relativedelta,
    batchDates: List[datetime],
    logger: Logger,
) -> List[List[Dict[str, Any]]]:

    query = buildPrRequestQuery(owner=owner, name=name, cursor=None)

    # prepare batches
    batches_pre: Dict[datetime, List[Dict[str, Any]]] = {
        date: [] for date in batchDates
    }
    current_time: datetime = datetime.now(batchDates[-1].tzinfo)
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
            created_at = isoparse(node["createdAt"])
            closed_at = (
                current_time if node["closedAt"] is None else isoparse(node["closedAt"])
            )

            authors: List[str] = list()
            for user_node in node["participants"]["nodes"]:
                gql.addLogin(node=user_node, authors=authors)

            pr: Dict[str, Any] = {
                "number": node["number"],
                "createdAt": created_at,
                "closedAt": closed_at,
                "comments": [
                    comment["bodyText"] for comment in node["comments"]["nodes"]
                ],
                "commitCount": node["commits"]["totalCount"],
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
        pageInfo = result["repository"]["pullRequests"]["pageInfo"]
        if not pageInfo["hasNextPage"]:
            # There is no next page to query
            no_next_page = True
        else:
            cursor = pageInfo["endCursor"]
            query = buildPrRequestQuery(owner=owner, name=name, cursor=cursor)

    return list(batches_pre.values())








def buildPrRequestQuery(owner: str, name: str, cursor: str):
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
        owner, name, gql.buildNextPageQuery(cursor)
    )
