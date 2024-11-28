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
from MLbackend.src.stats_analysis import outputStatistics
from MLbackend.src.utils import author_id_extractor
from MLbackend.src.utils.result import Result


def commit_analysis(
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
    start_date = None
    if config.start_date is not None:
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
        start_date = start_date.replace(tzinfo=pytz.UTC)
    batch_start_date = None
    batch_end_date = None
    batch_dates = []

    for commit in commits:
        if start_date is not None and start_date > commit.committed_datetime:
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
    author_info_dict = {}
    days_active = list()
    meta_results = []
    metric_results = []
    for idx, batch in enumerate(batches):

        # get batch authors

        batchAuthorInfoDict, batchDaysActive, meta_res, metric_res = (
            commit_batch_analysis(idx, senti, batch, config, logger, result)
        )
        meta_results.append(meta_res)
        metric_results.append(metric_res)

        # combine with main lists
        author_info_dict.update(batchAuthorInfoDict)
        days_active.append(batchDaysActive)

    return batch_dates, author_info_dict, days_active, meta_results[0], metric_results[0]


def commit_batch_analysis(
    idx: int,
    senti: PySentiStr,
    commits: List[git.Commit],
    config: Configuration,
    logger: Logger,
    result: Result,
):

    author_info_dict = {}
    timezone_info_dict = {}
    experience_days = 150

    # traverse all commits
    logger.info("Analyzing commits")
    start_date = None
    if config.start_date is not None:
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
        start_date = start_date.replace(tzinfo=pytz.UTC)
    # sort commits
    commits.sort(key=lambda o: o.committed_datetime, reverse=True)

    commit_messages = []
    commit: Commit
    last_date = None
    first_date = None
    real_commit_count = 0
    for commit in commits:
        if start_date is not None and start_date > commit.committed_datetime:
            continue
        if last_date is None:
            last_date = commit.committed_date
        first_date = commit.committed_date
        real_commit_count = real_commit_count + 1
        # extract info
        author = author_id_extractor(commit.author)
        timezone = commit.author_tz_offset
        time = commit.authored_datetime

        # get timezone
        timezone_info = timezone_info_dict.setdefault(
            timezone, dict(commit_count=0, authors=set())
        )

        # save info
        timezone_info["authors"].add(author)

        if commit.message and commit.message.strip():
            commit_messages.append(commit.message)

        # increase commit count
        timezone_info["commit_count"] += 1

        # get author
        author_info = author_info_dict.setdefault(
            author,
            dict(
                commit_count=0,
                sponsored_commit_count=0,
                earliestCommitDate=time,
                latestCommitDate=time,
                sponsored=False,
                active_days=0,
                experienced=False,
            ),
        )

        # increase commit count
        author_info["commit_count"] += 1

        # validate earliest commit
        # by default GitPython orders commits from latest to earliest
        if time < author_info["earliestCommitDate"]:
            author_info["earliestCommitDate"] = time

        # check if commit was between 9 and 5
        if not commit.author_tz_offset == 0 and time.hour >= 9 and time.hour <= 17:
            author_info["sponsored_commit_count"] += 1

    result.addTimeZoneCount(batch_idx=idx, timezone_count=len([*timezone_info_dict]))
    result.addCommitCount(batch_idx=idx, commit_count=real_commit_count)
    logger.info("Analyzing commit message sentiment")
    sentiment_scores = []
    commit_message_sentiments_positive = []
    commit_message_sentiments_negative = []

    if len(commit_messages) > 0:
        sentiment_scores = senti.getSentiment(commit_messages)
        commit_message_sentiments_positive = list(
            result for result in filter(lambda value: value >= 1, sentiment_scores)
        )
        commit_message_sentiments_negative = list(
            result for result in filter(lambda value: value <= -1, sentiment_scores)
        )

    logger.info("Analyzing authors")
    sponsored_author_count = 0
    for login, author in author_info_dict.items():

        # check if sponsored
        commit_count = int(author["commit_count"])
        sponsored_commit_count = int(author["sponsored_commit_count"])
        diff = sponsored_commit_count / commit_count
        if diff >= 0.95:
            author["sponsored"] = True
            sponsored_author_count += 1

        # calculate active days
        earliest_date = author["earliestCommitDate"]
        latest_date = author["latestCommitDate"]
        active_days = (latest_date - earliest_date).days + 1
        author["active_days"] = active_days

        # check if experienced
        if active_days >= experience_days:
            author["experienced"] = True

    # calculate percentage sponsored authors
    # In real world scenario it's not possible but for testing purpose.
    try:
        percentage_sponsored_authors = sponsored_author_count / len([*author_info_dict])
    except ZeroDivisionError:
        percentage_sponsored_authors = 0

    result.addAuthorCount(batch_idx=idx, author_count=len([*author_info_dict]))
    result.addSponsoredAuthorCount(
        batch_idx=idx, sponsored_author_count=sponsored_author_count
    )
    result.addPercentageSponsoredAuthor(
        batch_idx=idx, percentage_sponsored_author=percentage_sponsored_authors
    )

    # calculate active project days
    first_commit_date = None
    last_commit_date = None
    if first_date is not None:
        first_commit_date = datetime.fromtimestamp(first_date)
    if last_date is not None:
        last_commit_date = datetime.fromtimestamp(last_date)
    days_active = 0
    if last_commit_date is not None:
        days_active = (last_commit_date - first_commit_date).days
    result.addFirstCommitDate(batch_idx=idx, first_commit_date=first_commit_date)
    result.addLastCommitDate(batch_idx=idx, last_commit_date=last_commit_date)
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
        for login, author in author_info_dict.items():
            w.writerow([login, author["active_days"]])

    # output commits per author
    with open(
        os.path.join(config.metricsPath, f"commitsPerAuthor_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Author", "Commit Count"])
        for login, author in author_info_dict.items():
            w.writerow([login, author["commit_count"]])

    # output timezones
    with open(
        os.path.join(config.metricsPath, f"timezones_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["Timezone Offset", "Author Count", "Commit Count"])
        for key, timezone in timezone_info_dict.items():
            w.writerow([key, len(timezone["authors"]), timezone["commit_count"]])

    # output results
    with open(
        os.path.join(config.resultsPath, f"results_{idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["commit_count", real_commit_count])
        w.writerow(["days_active", days_active])
        w.writerow(["FirstCommitDate", "{:%Y-%m-%d}".format(first_commit_date)])
        w.writerow(["LastCommitDate", "{:%Y-%m-%d}".format(last_commit_date)])
        w.writerow(["AuthorCount", len([*author_info_dict])])
        w.writerow(["SponsoredAuthorCount", sponsored_author_count])
        w.writerow(["PercentageSponsoredAuthors", percentage_sponsored_authors])
        w.writerow(["TimezoneCount", len([*timezone_info_dict])])

    result_meta = [
        ["Metrics", "Value"],
        ["commit_count", real_commit_count],
        ["days_active", days_active],
        ["FirstCommitDate", "{:%Y-%m-%d}".format(first_commit_date)],
        ["LastCommitDate", "{:%Y-%m-%d}".format(last_commit_date)],
        ["AuthorCount", len([*author_info_dict])],
        ["SponsoredAuthorCount", sponsored_author_count],
        ["PercentageSponsoredAuthors", percentage_sponsored_authors],
        ["TimezoneCount", len([*timezone_info_dict])],
    ]

    metrics_data = [("Metric", "Count", "Mean", "Stdev")]

    active = outputStatistics(
        idx,
        [author["active_days"] for login, author in author_info_dict.items()],
        "AuthorActiveDays",
        config.resultsPath,
        logger,
        result,
    )

    commit_author = outputStatistics(
        idx,
        [author["commit_count"] for login, author in author_info_dict.items()],
        "AuthorCommitCount",
        config.resultsPath,
        logger,
        result,
    )

    times = outputStatistics(
        idx,
        [len(timezone["authors"]) for key, timezone in timezone_info_dict.items()],
        "TimezoneAuthorCount",
        config.resultsPath,
        logger,
        result,
    )

    times_commit = outputStatistics(
        idx,
        [timezone["commit_count"] for key, timezone in timezone_info_dict.items()],
        "TimezoneCommitCount",
        config.resultsPath,
        logger,
        result,
    )

    senti_msg = outputStatistics(
        idx,
        sentiment_scores,
        "CommitMessageSentiment",
        config.resultsPath,
        logger,
        result,
    )

    positive = outputStatistics(
        idx,
        commit_message_sentiments_positive,
        "CommitMessageSentimentsPositive",
        config.resultsPath,
        logger,
        result,
    )

    negative = outputStatistics(
        idx,
        commit_message_sentiments_negative,
        "CommitMessageSentimentsNegative",
        config.resultsPath,
        logger,
        result,
    )
    metrics_data.extend(
        [active, commit_author, times, times_commit, senti_msg, positive, negative]
    )

    return author_info_dict, days_active, result_meta, metrics_data
