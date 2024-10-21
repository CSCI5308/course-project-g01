import math
import os
import csv
import sys
from src.perspectiveAnalysis import getToxicityPercentage
import src.statsAnalysis as stats
import sentistrength
import src.graphqlAnalysis.graphqlAnalysisHelper as gql
import src.centralityAnalysis as centrality
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from typing import List, Dict, Any
from datetime import datetime, timezone
from src.configuration import Configuration
import threading
from typing import List, Tuple


def prAnalysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batchDates: List[datetime],
) -> Tuple[List[List[List[str]]], List[List[str]]]:

    print("Querying PRs")
    batches = prRequest(
        config.pat, config.repositoryOwner, config.repositoryName, delta, batchDates
    )

    batchParticipants = list()
    batchComments = list()

    for batchIdx, batch in enumerate(batches):
        print(f"Analyzing PR batch #{batchIdx}")

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

        print(f"    Sentiments per PR", end="")

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

        print("")

        # save comments
        batchComments.append(allComments)

        # get comment length stats
        commentLengths = [len(c) for c in allComments]

        try:
            generallyNegativeRatio = len(generallyNegative) / prCount
        except ZeroDivisionError:
            print(f"There are no PRs in batch #{batchIdx}")
            generallyNegativeRatio = 0

        # get pr duration stats
        durations = [(pr["closedAt"] - pr["createdAt"]).days for pr in batch]

        print("    All sentiments")

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

        toxicityPercentage = getToxicityPercentage(config, allComments)

        centrality.buildGraphQlNetwork(batchIdx, participants, "PRs", config)

        print("    Writing results")
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
        stats.outputStatistics(
            batchIdx,
            commentLengths,
            "PRCommentsLength",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            durations,
            "PRDuration",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            [len(pr["comments"]) for pr in batch],
            "PRCommentsCount",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            [pr["commitCount"] for pr in batch],
            "PRCommitsCount",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            commentSentiments,
            "PRCommentSentiments",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            [len(set(pr["participants"])) for pr in batch],
            "PRParticipantsCount",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            prPositiveComments,
            "PRCountPositiveComments",
            config.resultsPath,
        )

        stats.outputStatistics(
            batchIdx,
            prNegativeComments,
            "PRCountNegativeComments",
            config.resultsPath,
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

            print(f".", end="")


# def prRequest(
#     pat: str, owner: str, name: str, delta: relativedelta, batchDates: List[datetime]
# ):
#     query = buildPrRequestQuery(owner, name, None)

#     # prepare batches
#     batches = []
#     batch = None
#     batchStartDate = None
#     batchEndDate = None

#     while True:

#         # get page
#         result = gql.runGraphqlRequest(pat, query)
#         print("...")

#         # extract nodes
#         nodes = result["repository"]["pullRequests"]["nodes"]

#         # add results
#         for node in nodes:

#             createdAt = isoparse(node["createdAt"])
#             closedAt = (
#                 datetime.now(timezone.utc)
#                 if node["closedAt"] is None
#                 else isoparse(node["closedAt"])
#             )

#             if batchEndDate is None or (
#                 createdAt > batchEndDate and len(batches) < len(batchDates) - 1
#             ):

#                 if batch is not None:
#                     batches.append(batch)

#                 batchStartDate = batchDates[len(batches)]
#                 batchEndDate = batchStartDate + delta

#                 batch = []

#         pr = {
#                         "number": node["number"],
#                         "createdAt": createdAt,
#                         "closedAt": closedAt,
#                         "comments": list(c["bodyText"] for c in node["comments"]["nodes"]),
#                         "commitCount": node["commits"]["totalCount"],
#                         "participants": list(),
#                     }

#                     # participants
#                     for user in node["participants"]["nodes"]:
#                         gql.addLogin(user, pr["participants"])

#                     batch.append(pr)

#                 # check for next page
#                 pageInfo = result["repository"]["pullRequests"]["pageInfo"]
#                 if not pageInfo["hasNextPage"]:
#                     break

#                 cursor = pageInfo["endCursor"]
#                 query = buildPrRequestQuery(owner, name, cursor)

#     if batch is not None:
#         batches.append(batch)

#     return batches


# def prRequest(
#     pat: str, owner: str, name: str, delta: relativedelta, batchDates: List[datetime]
# ):
#     query = buildPrRequestQuery(owner, name, None)
#     print(query)
#     batches = []
#     current_batch_index = 0
#     result = gql.runGraphqlRequest(pat, query)
#     print(f"Batch length is {batchDates[0]} - {batchDates[0] + delta}")
#     for node in result["repository"]["pullRequests"]["nodes"]:
#         print(
#             isoparse(node["createdAt"]),
#             result["repository"]["pullRequests"]["pageInfo"]["hasNextPage"],
#         )
#     sys.exit()

#     # Ensure that batches are generated for all batch dates, even if no PR data exists
#     while current_batch_index < len(batchDates):
#         # Prepare current batch dates
#         batchStartDate = batchDates[current_batch_index]
#         batchEndDate = batchStartDate + delta
#         batch = []
#         print(
#             f"Current batch Index: {current_batch_index} and the date range is {batchStartDate} - {batchEndDate}"
#         )
#         nodes = result["repository"]["pullRequests"]["nodes"]

#         # Fetch PR data
#         while True:

#             for node in nodes:
#                 createdAt = isoparse(node["createdAt"])
#                 closedAt = (
#                     datetime.now(timezone.utc)
#                     if node["closedAt"] is None
#                     else isoparse(node["closedAt"])
#                 )

#                 # Only process PRs within the current batch's date range
#                 if batchStartDate <= createdAt < batchEndDate:
#                     pr = {
#                         "number": node["number"],
#                         "createdAt": createdAt,
#                         "closedAt": closedAt,
#                         "comments": [c["bodyText"] for c in node["comments"]["nodes"]],
#                         "commitCount": node["commits"]["totalCount"],
#                         "participants": [],
#                     }

#                     # Add participants
#                     for user in node["participants"]["nodes"]:
#                         gql.addLogin(user, pr["participants"])

#                     batch.append(pr)

#             # Check for the next page
#             pageInfo = result["repository"]["pullRequests"]["pageInfo"]
#             print(f"Next page exists: {pageInfo['hasNextPage']}")
#             if not pageInfo["hasNextPage"]:
#                 break

#             # Update query with next page cursor
#             cursor = pageInfo["endCursor"]
#             query = buildPrRequestQuery(owner, name, cursor)

#         # Append the batch (empty or not) to batches
#         batches.append(batch)
#         current_batch_index += 1  # Move to the next batch date

#     return batches


def prRequest(
    pat: str, owner: str, name: str, delta: relativedelta, batchDates: List[datetime]
) -> None:

    query = buildPrRequestQuery(owner=owner, name=name, cursor=None)

    # prepare batches
    batches_pre: Dict[datetime, List[Dict[str, Any]]] = {
        date: [] for date in batchDates
    }
    batches_pre[datetime.now(batchDates[-1].tzinfo)] = []
    no_next_page: bool = False

    while not no_next_page:

        # Get a chunk of page
        result = gql.runGraphqlRequest(pat, query)
        print("...")

        # Get all the nodes in the result
        nodes = result["repository"]["pullRequests"]["nodes"]

        # Add all nodes that are required
        for node in nodes:
            created_at = isoparse(node["createdAt"])
            closed_at = (
                datetime.now(timezone.utc)
                if node["closedAt"] is None
                else isoparse(node["closedAt"])
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

            batch_date: datetime

            for date in batches_pre.keys():
                batch_date = date
                if date <= created_at < date + delta:
                    # This means we have exceeded the range by 1
                    break

            batches_pre[batch_date].append(pr)

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
