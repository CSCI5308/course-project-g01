import os
import git
import csv
import datetime
from logging import Logger

from progress.bar import Bar
from src.statsAnalysis import outputStatistics
from typing import List
from dateutil.relativedelta import relativedelta
from src.configuration import Configuration


def tagAnalysis(
    repo: git.Repo,
    delta: relativedelta,
    batchDates: List[datetime.datetime],
    daysActive: List[int],
    config: Configuration,
    logger: Logger,
) -> None:
    logger.info("Analyzing tags")

    tagInfo = []
    logger.info("Sorting tags")
    tags = sorted(repo.tags, key=getTaggedDate)

    # get tag list
    if len(tags) > 0:
        lastTag = None
        for tag in tags:
            commitCount = 0
            if lastTag is None:
                commitCount = len(list(tag.commit.iter_items(repo, tag.commit)))
            else:
                sinceStr = formatDate(getTaggedDate(lastTag))
                commitCount = len(
                    list(tag.commit.iter_items(repo, tag.commit, after=sinceStr))
                )

            tagInfo.append(
                dict(
                    path=tag.path,
                    rawDate=getTaggedDate(tag),
                    date=formatDate(getTaggedDate(tag)),
                    commitCount=commitCount,
                )
            )

            lastTag = tag

    # output tag batches
    for idx, batchStartDate in enumerate(batchDates):
        batchEndDate = batchStartDate + delta

        batchTags = [
            tag
            for tag in tagInfo
            if tag["rawDate"] >= batchStartDate and tag["rawDate"] < batchEndDate
        ]

        outputTags(idx, batchTags, daysActive[idx], config, logger)


def outputTags(
    idx: int,
    tagInfo: List[dict],
    daysActive: int,
    config: Configuration,
    logger: Logger,
):

    # calculate FN
    try:
        fn = len(tagInfo) / daysActive * 100
    except ZeroDivisionError:
        fn: float = 0
        logger.warning(f"Number of days active is 0 for tag at date {tagInfo['date']}.")

    # output non-tabular results
    with open(
        os.path.join(config.resultsPath, f"results_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Tag Count", len(tagInfo)])

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
        for tag in tagInfo:
            w.writerow([tag["path"], tag["date"], tag["commitCount"]])

    outputStatistics(
        idx,
        [tag["commitCount"] for tag in tagInfo],
        "TagCommitCount",
        config.resultsPath,
        logger,
    )


def getTaggedDate(tag):
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


def formatDate(value):
    return value.strftime("%Y-%m-%d")
