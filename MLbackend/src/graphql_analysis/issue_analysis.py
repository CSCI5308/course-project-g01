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

def issue_analysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger, 
    result:Result   

):

    logger.info("Querying issue comments")
    batches = issue_request(
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
        generally_negative, issue_count, all_comments, participants, comment_lengths, issue_positive_comments, issue_negative_comments = get_stats(logger=logger, batch_idx=batch_idx, batch_participants=batch_participants, senti=senti, batch_comments=batch_comments, batch=batch, stat_type="Issue")


        try:
            generally_negative_ratio = len(generally_negative) / issue_count
        except ZeroDivisionError:
            generally_negative_ratio = 0
            logger.warning(
                f"There are no Issues for batch #{batch_idx} setting generally negative ratio as 0."
            )

        # get pr duration stats
        durations, comment_sentiments, comment_sentiments_positive, comment_sentiments_negative, toxicity_percentage = get_comment_stats(all_comments=all_comments, senti=senti, config=config, logger=logger, batch=batch)


        author, meta, metrics_data = centrality.build_grapql_network(batch_idx, participants, "Issues", config, logger, result)

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
            w.writerow(["IssueCommentsToxicityPercentage", toxicity_percentage])

        meta1 = [
            ["Metrics", "Issue"],
            ["NumberIssues", len(batch)],
            ["NumberIssueComments", len(all_comments)],
            ["IssueCommentsPositive", comment_sentiments_positive],
            ["IssueCommentsNegative", comment_sentiments_negative],
            ["IssueCommentsNegativeRatio", generally_negative_ratio],
            ["IssueCommentsToxicityPercentage", toxicity_percentage],
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
        issue_len = stats.output_statistics(
            batch_idx,
            comment_lengths,
            "IssueCommentsLength",
            config.resultsPath,
            logger,
        )

        issue_dur = stats.output_statistics(
            batch_idx,
            durations,
            "IssueDuration",
            config.resultsPath,
            logger,
        )

        issue_com = stats.output_statistics(
            batch_idx,
            [len(issue["comments"]) for issue in batch],
            "IssueCommentsCount",
            config.resultsPath,
            logger,
        )

        sent = stats.output_statistics(
            batch_idx,
            comment_sentiments,
            "IssueCommentSentiments",
            config.resultsPath,
            logger,
        )

        part = stats.output_statistics(
            batch_idx,
            [len(set(issue["participants"])) for issue in batch],
            "IssueParticipantCount",
            config.resultsPath,
            logger,
        )

        pos = stats.output_statistics(
            batch_idx,
            issue_positive_comments,
            "IssueCountPositiveComments",
            config.resultsPath,
            logger,
        )

        neg = stats.output_statistics(
            batch_idx,
            issue_negative_comments,
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





def issue_request(
    pat: str,
    owner: str,
    name: str,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
) -> list[list[dict[str, Any]]]:

    query = build_issue_request_query(owner=owner, name=name, cursor=None)

    batches_pre: Dict[datetime, List[Dict[str, Any]]] = {
        date: [] for date in batch_dates
    }
    current_time: datetime = datetime.now(batch_dates[-1].tzinfo)

    no_next_page: bool = False

    while not no_next_page:

        # Get chunk of page
        result = gql.run_graphql_request(pat=pat, query=query, logger=logger)

        # Get all the nodes in the result
        try:
            nodes = result["repository"]["issues"]["nodes"]
        except TypeError:
            # There are no PRs in this repository
            logger.error("There are no Issues for this repository")
            break

        # Add all nodes that are required
        for node in nodes:

            created_at: datetime = isoparse(node["createdAt"])
            closed_at: datetime = (
                current_time if node["closedAt"] is None else isoparse(node["closedAt"])
            )

            # Get all the authors
            authors: List[str] = list()
            for user_node in node["participants"]["nodes"]:
                gql.add_login(node=user_node, authors=authors)

            # Create the issue dictionary
            issue: Dict[str, Any] = {
                "number": node["number"],
                "created_at": created_at,
                "closed_at": closed_at,
                "comments": [
                    comment["bodyText"] for comment in node["comments"]["nodes"]
                ],
                "participants": authors,
            }

            batches_pre = create_analysis_batches(batches_pre=batches_pre, created_at=created_at, delta=delta, entity=issue, current_time=current_time)

        # Check for next page
        page_info = result["repository"]["issues"]["pageInfo"]
        if not page_info["hasNextPage"]:
            no_next_page = True
        else:
            cursor = page_info["endCursor"]
            query = build_issue_request_query(owner=owner, name=name, cursor=cursor)

    return list(batches_pre.values())


def build_issue_request_query(owner: str, name: str, cursor: str | None):
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
        owner, name, gql.build_next_page_query(cursor)
    )
