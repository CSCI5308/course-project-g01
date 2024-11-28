import csv
import os
from datetime import datetime
from logging import Logger
from typing import List

import git
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

import MLbackend.src.graphql_analysis.graphql_analysis_helper as gql
import MLbackend.src.stats_analysis as stats
from MLbackend.src.configuration import Configuration


def release_analysis(
    all_commits: List[git.Commit],
    config: Configuration,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
) -> None:

    # sort commits by ascending commit date
    all_commits.sort(key=lambda c: c.committed_datetime)

    logger.info("Querying releases")
    batches = releaseRequest(config, delta, batch_dates, logger)

    if not batches:
        logger.warning("No batches found.")
        return  # Exit the function if no batches are found

    for batch_idx, batch in enumerate(batches):

        releases = batch["releases"]
        release_authors = set()
        release_commits_count = {}

        for i, release in enumerate(releases):
            release_commits = list()
            release_date = release["created_at"]

            # try add author to set
            release_authors.add(release["author"])

            if i == 0:

                # this is the first release, get all commits prior to release created date
                for commit in all_commits:
                    if commit.committed_datetime < release_date:
                        release_commits.append(commit)
                    else:
                        break

            else:

                # get in-between commit count
                prev_release_date = releases[i - 1]["created_at"]
                for commit in all_commits:
                    if (
                        commit.committed_datetime >= prev_release_date
                        and commit.committed_datetime < release_date
                    ):
                        release_commits.append(commit)
                    else:
                        break

            # remove all counted commits from list to improve iteration speed
            all_commits = all_commits[len(release_commits) :]

            # calculate authors per release
            commit_authors = set(commit.author.email for commit in release_commits)

            # add results
            release_commits_count[release["name"]] = dict(
                date=release["created_at"],
                authorsCount=len(commit_authors),
                commitsCount=len(release_commits),
            )

        # sort releases by date ascending
        release_commits_count = {
            key: value
            for key, value in sorted(
                release_commits_count.items(), key=lambda r: r[1]["date"]
            )
        }

        logger.info("Writing results for analysis of releases to CSVs.")
        with open(
            os.path.join(config.resultsPath, f"results_{batch_idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["NumberReleases", batch["releaseCount"]])
            w.writerow(["NumberReleaseAuthors", len(release_authors)])

        with open(
            os.path.join(config.metricsPath, f"releases_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Release", "Date", "Author Count", "Commit Count"])
            for key, value in release_commits_count.items():
                w.writerow(
                    [
                        key,
                        value["date"].isoformat(),
                        value["authorsCount"],
                        value["commitsCount"],
                    ]
                )

        stats.outputStatistics(
            batch_idx,
            [value["authorsCount"] for key, value in release_commits_count.items()],
            "ReleaseAuthorCount",
            config.resultsPath,
            logger,
        )

        stats.outputStatistics(
            batch_idx,
            [value["commitsCount"] for key, value in release_commits_count.items()],
            "ReleaseCommitCount",
            config.resultsPath,
            logger,
        )
        return release_commits_count


def releaseRequest(
    config: Configuration,
    delta: relativedelta,
    batch_dates: List[datetime],
    logger: Logger,
):
    query = build_release_request_query(
        config.repositoryOwner, config.repositoryName, None
    )

    # prepare batches
    batches = []
    batch = None
    batch_start_date = None
    batch_end_date = None

    while True:

        # get page of releases
        result = gql.runGraphqlRequest(config.pat, query, logger)

        # extract nodes
        try:
            nodes = result["repository"]["releases"]["nodes"]
        except TypeError:
            # There are no releases present
            logger.error("There are no releases for this repository")
            break

        # parse
        for node in nodes:

            created_at = isoparse(node["created_at"])

            if batch_end_date is None or (
                created_at > batch_end_date and len(batches) < len(batch_dates) - 1
            ):

                if batch is not None:
                    batches.append(batch)

                batch_start_date = batch_dates[len(batches)]
                batch_end_date = batch_start_date + delta

                batch = {"releaseCount": 0, "releases": []}

            batch["releaseCount"] += 1
            batch["releases"].append(
                dict(
                    name=node["name"],
                    created_at=created_at,
                    author=node["author"]["login"],
                )
            )

        # check for next page
        page_info = result["repository"]["releases"]["page_info"]

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        query = build_release_request_query(
            config.repositoryOwner, config.repositoryName, cursor
        )

    if batch is not None:
        batches.append(batch)

    return batches


def build_release_request_query(owner: str, name: str, cursor: str):
    return """{{
        repository(owner: "{0}", name: "{1}") {{
            releases(first:100{2}) {{
                totalCount
                nodes {{
                    author {{
                        login
                    }}
                    created_at
                    name
                }}
                page_info {{
                    endCursor
                    hasNextPage
                }}
            }}
        }}
    }}""".format(
        owner, name, gql.build_next_page_query(cursor)
    )
