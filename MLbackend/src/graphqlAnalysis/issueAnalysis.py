import os
import csv
import math
import sys
import src.statsAnalysis as stats
import sentistrength
import src.graphqlAnalysis.graphqlAnalysisHelper as gql
import src.centralityAnalysis as centrality
from logging import Logger
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from typing import List, Any, Dict
from datetime import datetime, timezone
from src.configuration import Configuration
import threading
from src.perspectiveAnalysis import getToxicityPercentage


def issueAnalysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batchDates: List[datetime],
    logger: Logger,
):

    logger.info("Querying issue comments")
    batches = issueRequest(
        config.pat,
        config.repositoryOwner,
        config.repositoryName,
        delta,
        batchDates,
        logger,
    )

    batchParticipants = list()
    batchComments = list()

    for batchIdx, batch in enumerate(batches):
        logger.info(f"Analyzing issue batch #{batchIdx}")

        # extract data from batch
        issueCount = len(batch)
        participants = list(
            issue["participants"] for issue in batch if len(issue["participants"]) > 0
        )
        batchParticipants.append(participants)

        allComments = list()
        issuePositiveComments = list()
        issueNegativeComments = list()
        generallyNegative = list()

        semaphore = threading.Semaphore(15)
        threads = []
        for issue in batch:
            comments = list(
                comment for comment in issue["comments"] if comment and comment.strip()
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
                issuePositiveComments.append(0)
                issueNegativeComments.append(0)
                continue

            allComments.extend(comments)

            thread = threading.Thread(
                target=analyzeSentiments,
                args=(
                    senti,
                    comments,
                    issuePositiveComments,
                    issueNegativeComments,
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
            generallyNegativeRatio = len(generallyNegative) / issueCount
        except ZeroDivisionError:
            generallyNegativeRatio = 0
            logger.warning(
                f"There are no Issues for batch #{batchIdx} setting generally negative ratio as 0."
            )

        # get pr duration stats
        durations = [(pr["closedAt"] - pr["createdAt"]).days for pr in batch]

        # analyze comment issue sentiment
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

        centrality.buildGraphQlNetwork(batchIdx, participants, "Issues", config, logger)

        logger.info("Writing GraphQL analysis results")
        with open(
            os.path.join(config.resultsPath, f"results_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["NumberIssues", len(batch)])
            w.writerow(["NumberIssueComments", len(allComments)])
            w.writerow(["IssueCommentsPositive", commentSentimentsPositive])
            w.writerow(["IssueCommentsNegative", commentSentimentsNegative])
            w.writerow(["IssueCommentsNegativeRatio", generallyNegativeRatio])
            w.writerow(["IssueCommentsToxicityPercentage", toxicityPercentage])

        with open(
            os.path.join(config.metricsPath, f"issueCommentsCount_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Issue Number", "Comment Count"])
            for issue in batch:
                w.writerow([issue["number"], len(issue["comments"])])

        with open(
            os.path.join(config.metricsPath, f"issueParticipantCount_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Issue Number", "Developer Count"])
            for issue in batch:
                w.writerow([issue["number"], len(set(issue["participants"]))])

        # output statistics
        stats.outputStatistics(
            batchIdx, commentLengths, "IssueCommentsLength", config.resultsPath, logger
        )

        stats.outputStatistics(
            batchIdx, durations, "IssueDuration", config.resultsPath, logger
        )

        stats.outputStatistics(
            batchIdx,
            [len(issue["comments"]) for issue in batch],
            "IssueCommentsCount",
            config.resultsPath,
            logger,
        )

        stats.outputStatistics(
            batchIdx,
            commentSentiments,
            "IssueCommentSentiments",
            config.resultsPath,
            logger,
        )

        stats.outputStatistics(
            batchIdx,
            [len(set(issue["participants"])) for issue in batch],
            "IssueParticipantCount",
            config.resultsPath,
            logger,
        )

        stats.outputStatistics(
            batchIdx,
            issuePositiveComments,
            "IssueCountPositiveComments",
            config.resultsPath,
            logger,
        )

        stats.outputStatistics(
            batchIdx,
            issueNegativeComments,
            "IssueCountNegativeComments",
            config.resultsPath,
            logger,
        )

    return batchParticipants, batchComments


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
    batches_pre[current_time] = []

    no_next_page: bool = False

    while not no_next_page:

        # Get chunk of page
        result = gql.runGraphqlRequest(pat=pat, query=query, logger=logger)

        # Get all the nodes in the result
        nodes = result["repository"]["issues"]["nodes"]

        # Add all nodes that are required
        for node in nodes:

            created_at: datetime = isoparse(node["createdAt"])
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
                "createdAt": created_at,
                "closedAt": closed_at,
                "comments": [
                    comment["bodyText"] for comment in node["comments"]["nodes"]
                ],
                "participants": authors,
            }

            batch_date: datetime

            for date in batches_pre.keys():
                batch_date = date
                if date <= created_at < date + delta:
                    # This means we have exceeded the range by 1
                    break

            batches_pre[batch_date].append(issue)

        # Check for next page
        page_info = result["repository"]["issues"]["pageInfo"]
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
                pageInfo {{
                    hasNextPage
                    endCursor
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
