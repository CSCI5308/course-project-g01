import csv
import os
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Tuple

import git
import pytz
from dateutil.relativedelta import relativedelta
from git.objects.commit import Commit
from sentistrength import PySentiStr

from MLbackend.src.configuration import Configuration
from MLbackend.src.statsAnalysis import outputStatistics
from MLbackend.src.utils import author_id_extractor
from MLbackend.src.utils.result import Result


def commitAnalysis(
    senti: PySentiStr,
    commits: List[git.Commit],
    delta: relativedelta,
    config: Configuration,
    logger: Logger,
    result: Result,
) -> Tuple[List[datetime], Dict[str, Dict[str, Any]], List[int]]:

    # sort commits
    commits.sort(key=lambda o: o.committed_datetime)

    # split commits into batches
    batches = []
    batch = []
    startDate = None
    if config.startDate is not None:
        startDate = datetime.strptime(config.startDate, "%Y-%m-%d")
        startDate = startDate.replace(tzinfo=pytz.UTC)
    batch_start_date = None
    batch_end_date = None
    batch_dates = []

    for commit in commits:
        if startDate is not None and startDate > commit.committed_datetime:
            continue
        # prepare first batch
        if batch_start_date is None:
            batch_start_date = commit.committed_datetime
            batch_end_date = batch_start_date + delta

            batch_dates.append(batch_start_date)
            result.addBatchDates([batch_start_date])

        # prepare next batch
        elif commit.committed_datetime > batch_end_date:
            batches.append(batch)
            batch = []
            batch_start_date = commit.committed_datetime
            batch_end_date = batch_start_date + delta

            batch_dates.append(batch_start_date)
            result.addBatchDates([batch_start_date])

        # populate current batch
        batch.append(commit)

    # complete batch list and perform clean up
    batches.append(batch)
    del batch, commits

    # run analysis per batch
    authorInfoDict = {}
    days_active = list()
    meta_results = []
    metric_results = []
    for idx, batch in enumerate(batches):

        # get batch authors

        batchAuthorInfoDict, batchDaysActive, meta_res, metric_res = (
            commitBatchAnalysis(idx, senti, batch, config, logger, result)
        )
        meta_results.append(meta_res)
        metric_results.append(metric_res)

        # combine with main lists
        authorInfoDict.update(batchAuthorInfoDict)
        days_active.append(batchDaysActive)

    return batch_dates, authorInfoDict, days_active, meta_results[0], metric_results[0]


def commitBatchAnalysis(
    idx: int,
    senti: PySentiStr,
    commits: List[git.Commit],
    config: Configuration,
    logger: Logger,
    result: Result,
):

    authorInfoDict = {}
    timezoneInfoDict = {}
    experienceDays = 150

    # traverse all commits
    logger.info("Analyzing commits")
    startDate = None
    if config.startDate is not None:
        startDate = datetime.strptime(config.startDate, "%Y-%m-%d")
        startDate = startDate.replace(tzinfo=pytz.UTC)
    # sort commits
    commits.sort(key=lambda o: o.committed_datetime, reverse=True)

    commitMessages = []
    commit: Commit
    lastDate = None
    firstDate = None
    realCommitCount = 0
    for commit in commits:
        if startDate is not None and startDate > commit.committed_datetime:
            continue
        if lastDate is None:
            lastDate = commit.committed_date
        firstDate = commit.committed_date
        realCommitCount = realCommitCount + 1
        # extract info
        author = author_id_extractor(commit.author)
        timezone = commit.author_tz_offset
        time = commit.authored_datetime

        # get timezone
        timezoneInfo = timezoneInfoDict.setdefault(
            timezone, dict(commit_count=0, authors=set())
        )

        # save info
        timezoneInfo["authors"].add(author)

        if commit.message and commit.message.strip():
            commitMessages.append(commit.message)

        # increase commit count
        timezoneInfo["commit_count"] += 1

        # get author
        authorInfo = authorInfoDict.setdefault(
            author,
            dict(
                commit_count=0,
                sponsoredCommitCount=0,
                earliestCommitDate=time,
                latestCommitDate=time,
                sponsored=False,
                activeDays=0,
                experienced=False,
            ),
        )

        # increase commit count
        authorInfo["commit_count"] += 1

        # validate earliest commit
        # by default GitPython orders commits from latest to earliest
        if time < authorInfo["earliestCommitDate"]:
            authorInfo["earliestCommitDate"] = time

        # check if commit was between 9 and 5
        if not commit.author_tz_offset == 0 and time.hour >= 9 and time.hour <= 17:
            authorInfo["sponsoredCommitCount"] += 1

    result.addTimeZoneCount(batch_idx=idx, timezone_count=len([*timezoneInfoDict]))
    result.addCommitCount(batch_idx=idx, commit_count=realCommitCount)
    logger.info("Analyzing commit message sentiment")
    sentimentScores = []
    commitMessageSentimentsPositive = []
    commitMessageSentimentsNegative = []

    if len(commitMessages) > 0:
        sentimentScores = senti.getSentiment(commitMessages)
        commitMessageSentimentsPositive = list(
            result for result in filter(lambda value: value >= 1, sentimentScores)
        )
        commitMessageSentimentsNegative = list(
            result for result in filter(lambda value: value <= -1, sentimentScores)
        )

    logger.info("Analyzing authors")
    sponsoredAuthorCount = 0
    for login, author in authorInfoDict.items():

        # check if sponsored
        commit_count = int(author["commit_count"])
        sponsoredCommitCount = int(author["sponsoredCommitCount"])
        diff = sponsoredCommitCount / commit_count
        if diff >= 0.95:
            author["sponsored"] = True
            sponsoredAuthorCount += 1

        # calculate active days
        earliestDate = author["earliestCommitDate"]
        latestDate = author["latestCommitDate"]
        activeDays = (latestDate - earliestDate).days + 1
        author["activeDays"] = activeDays

        # check if experienced
        if activeDays >= experienceDays:
            author["experienced"] = True

    # calculate percentage sponsored authors
    # In real world scenario it's not possible but for testing purpose.
    try:
        percentageSponsoredAuthors = sponsoredAuthorCount / len([*authorInfoDict])
    except ZeroDivisionError:
        percentageSponsoredAuthors = 0

    result.addAuthorCount(batch_idx=idx, author_count=len([*authorInfoDict]))
    result.addSponsoredAuthorCount(
        batch_idx=idx, sponsored_author_count=sponsoredAuthorCount
    )
    result.addPercentageSponsoredAuthor(
        batch_idx=idx, percentage_sponsored_author=percentageSponsoredAuthors
    )

    # calculate active project days
    firstCommitDate = None
    lastCommitDate = None
    if firstDate is not None:
        firstCommitDate = datetime.fromtimestamp(firstDate)
    if lastDate is not None:
        lastCommitDate = datetime.fromtimestamp(lastDate)
    days_active = 0
    if lastCommitDate is not None:
        days_active = (lastCommitDate - firstCommitDate).days
    result.addFirstCommitDate(batch_idx=idx, first_commit_date=firstCommitDate)
    result.addLastCommitDate(batch_idx=idx, last_commit_date=lastCommitDate)
    result.addDaysActive(batch_idx=idx, days_active=days_active)

    logger.info("Outputting CSVs")

    # output author days on project
    with open(
        os.path.join(config.metricsPath, f"authorDaysOnProject_{idx}.csv"),
        "a",
        newline="",
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Author", "# of Days"])
        for login, author in authorInfoDict.items():
            w.writerow([login, author["activeDays"]])

    # output commits per author
    with open(
        os.path.join(config.metricsPath, f"commitsPerAuthor_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Author", "Commit Count"])
        for login, author in authorInfoDict.items():
            w.writerow([login, author["commit_count"]])

    # output timezones
    with open(
        os.path.join(config.metricsPath, f"timezones_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Timezone Offset", "Author Count", "Commit Count"])
        for key, timezone in timezoneInfoDict.items():
            w.writerow([key, len(timezone["authors"]), timezone["commit_count"]])

    # output results
    with open(
        os.path.join(config.resultsPath, f"results_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["commit_count", realCommitCount])
        w.writerow(["days_active", days_active])
        w.writerow(["FirstCommitDate", "{:%Y-%m-%d}".format(firstCommitDate)])
        w.writerow(["LastCommitDate", "{:%Y-%m-%d}".format(lastCommitDate)])
        w.writerow(["AuthorCount", len([*authorInfoDict])])
        w.writerow(["SponsoredAuthorCount", sponsoredAuthorCount])
        w.writerow(["PercentageSponsoredAuthors", percentageSponsoredAuthors])
        w.writerow(["TimezoneCount", len([*timezoneInfoDict])])

    result_meta = [
        ["Metrics", "Value"],
        ["commit_count", realCommitCount],
        ["days_active", days_active],
        ["FirstCommitDate", "{:%Y-%m-%d}".format(firstCommitDate)],
        ["LastCommitDate", "{:%Y-%m-%d}".format(lastCommitDate)],
        ["AuthorCount", len([*authorInfoDict])],
        ["SponsoredAuthorCount", sponsoredAuthorCount],
        ["PercentageSponsoredAuthors", percentageSponsoredAuthors],
        ["TimezoneCount", len([*timezoneInfoDict])],
    ]

    metrics_data = [("Metric", "Count", "Mean", "Stdev")]

    active = outputStatistics(
        idx,
        [author["activeDays"] for login, author in authorInfoDict.items()],
        "AuthorActiveDays",
        config.resultsPath,
        logger,
        result,
    )

    commit_author = outputStatistics(
        idx,
        [author["commit_count"] for login, author in authorInfoDict.items()],
        "AuthorCommitCount",
        config.resultsPath,
        logger,
        result,
    )

    times = outputStatistics(
        idx,
        [len(timezone["authors"]) for key, timezone in timezoneInfoDict.items()],
        "TimezoneAuthorCount",
        config.resultsPath,
        logger,
        result,
    )

    times_commit = outputStatistics(
        idx,
        [timezone["commit_count"] for key, timezone in timezoneInfoDict.items()],
        "TimezoneCommitCount",
        config.resultsPath,
        logger,
        result,
    )

    senti_msg = outputStatistics(
        idx,
        sentimentScores,
        "CommitMessageSentiment",
        config.resultsPath,
        logger,
        result,
    )

    positive = outputStatistics(
        idx,
        commitMessageSentimentsPositive,
        "CommitMessageSentimentsPositive",
        config.resultsPath,
        logger,
        result,
    )

    negative = outputStatistics(
        idx,
        commitMessageSentimentsNegative,
        "CommitMessageSentimentsNegative",
        config.resultsPath,
        logger,
        result,
    )
    metrics_data.extend(
        [active, commit_author, times, times_commit, senti_msg, positive, negative]
    )

    return authorInfoDict, days_active, result_meta, metrics_data
