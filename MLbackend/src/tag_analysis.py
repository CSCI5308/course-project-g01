import csv
import datetime
import os
from logging import Logger
from typing import List, Any

import git
from dateutil.relativedelta import relativedelta

from MLbackend.src.configuration import Configuration
from MLbackend.src.stats_analysis import output_statistics


def tag_analysis(
    repo: git.Repo,
    delta: relativedelta,
    batch_dates: List[datetime.datetime],
    days_active: List[int],
    config: Configuration,
    logger: Logger,
) -> list[list[Any]]:
    logger.info("Analyzing tags")

    tag_info = []
    logger.info("Sorting tags")
    tags = sorted(repo.tags, key=get_tagged_date)

    # get tag list
    if len(tags) > 0:
        last_tag = None
        for tag in tags:
            commit_count = 0
            if last_tag is None:
                commit_count = len(list(tag.commit.iter_items(repo, tag.commit)))
            else:
                since_str = format_date(get_tagged_date(last_tag))
                commit_count = len(
                    list(tag.commit.iter_items(repo, tag.commit, after=since_str))
                )

            tag_info.append(
                dict(
                    path=tag.path,
                    rawDate=get_tagged_date(tag),
                    date=format_date(get_tagged_date(tag)),
                    commit_count=commit_count,
                )
            )

            last_tag = tag

    # output tag batches
    res = []
    for idx, batch_start_date in enumerate(batch_dates):
        batch_end_date = batch_start_date + delta

        batch_tags = [
            tag
            for tag in tag_info
            if batch_start_date <= tag["rawDate"] < batch_end_date
        ]

        x = outputTags(idx, batch_tags, days_active[idx], config, logger)
        res.append(x)
    return res


def outputTags(
    idx: int,
    tag_info: List[dict],
    days_active: int,
    config: Configuration,
    logger: Logger,
):

    # calculate FN
    try:
        fn = len(tag_info) / days_active * 100
    except ZeroDivisionError:
        fn: float = 0
        logger.warning(f"Number of days active is 0 for tag at date {tag_info}.")

    # output non-tabular results
    with open(
        os.path.join(config.resultsPath, f"results_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Tag Count", len(tag_info)])

    # output tag info
    logger.info("Outputting CSVs with tag information.")

    with open(
        os.path.join(config.resultsPath, f"results_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["FN", fn])

    with open(
        os.path.join(config.metricsPath, f"tags_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Path", "Date", "Commit Count"])
        for tag in tag_info:
            w.writerow([tag["path"], tag["date"], tag["commit_count"]])

    output_statistics(
        idx,
        [tag["commit_count"] for tag in tag_info],
        "TagCommitCount",
        config.resultsPath,
        logger,
    )
    return [tag["commit_count"] for tag in tag_info]


def get_tagged_date(tag):
    date = None

    if tag.tag is None:
        date = tag.commit.committed_datetime
    else:

        # get timezone
        offset = tag.tag.tagger_tz_offset
        tzinfo = datetime.timezone(-datetime.timedelta(seconds=offset))

        # get aware date from timestamp
        date = tag.tag.tagged_date
        date = datetime.datetime.fromtimestamp(date, tzinfo)

    return date


def format_date(value):
    return value.strftime("%Y-%m-%d")
