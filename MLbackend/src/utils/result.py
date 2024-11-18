from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Tuple


class Result:

    def __init__(self, logger: Logger) -> None:

        self._batch_dates: List[datetime] = []
        self._commit_count: List[int] = []
        self._core_devs: List[str] = []
        self._days_active: List[int] = []
        self._first_commit_dates: List[str] = []
        self._last_commit_dates: List[str] = []
        self._author_counts: List[int] = []
        self._sponsored_author_counts: List[int] = []
        self._percentage_sponsored_authors: List[int] = []
        self._timezone_counts: List[int] = []
        self._metric_datas: List[Tuple[str, int, float, float]] = []
        self._smells: List[List[str]] = []
        self._pr_counts: List[int] = []
        self._pr_comment_counts: List[int] = []
        self._pr_comment_sentiment_positive_counts: List[int] = []
        self._pr_comment_sentiment_negative_counts: List[int] = []
        self._pr_comment_sentiment_negative_ratios: List[int] = []
        self.logger: Logger = logger
        self.pdf_file_path: Path

        return None

    def setPDFFilePath(self, pdf_file_path: Path) -> None:
        self.pdf_file_path = pdf_file_path

    @property
    def commit_count(self) -> List[int]:
        return self._commit_count

    @commit_count.setter
    def commit_count(self, commit_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'commit_count' is not allowed. Use method addCommitCount to modify this property based on the requirement."
        )

    @property
    def pr_count(self) -> List[int]:
        return self._pr_counts

    @pr_count.setter
    def pr_count(self, pr_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'pr_count' is not allowed. Use method addPRCount to modify this property based on the requirement."
        )

    @property
    def pr_comment_count(self) -> List[int]:
        return self._pr_comment_counts

    @pr_comment_count.setter
    def pr_comment_count(self, pr_comment_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'pr_comment_count' is not allowed. Use method addPRCommentCount to modify this pr_comment property based on the requirement."
        )

    @property
    def pr_comment_sentiment_positive_count(self) -> List[int]:
        return self._pr_comment_sentiment_positive_counts

    @pr_comment_sentiment_positive_count.setter
    def pr_comment_sentiment_positive_count(
        self, pr_comment_sentiment_positive_counts: List[int]
    ) -> None:
        raise AttributeError(
            "Direct assignment to 'pr_comment_sentiment_positive_count' is not allowed. Use method addPRCommentSentimentPositiveCount to modify this pr_comment_sentiment_positive property based on the requirement."
        )

    @property
    def pr_comment_sentiment_negative_count(self) -> List[int]:
        return self._pr_comment_sentiment_negative_counts

    @pr_comment_sentiment_negative_count.setter
    def pr_comment_sentiment_negative_count(
        self, pr_comment_sentiment_negative_counts: List[int]
    ) -> None:
        raise AttributeError(
            "Direct assignment to 'pr_comment_sentiment_negative_count' is not allowed. Use method addPRCommentSentimentNegativeCount to modify this pr_comment_sentiment_negative property based on the requirement."
        )

    @property
    def pr_comment_sentiment_negative_ratio(self) -> List[int]:
        return self._pr_comment_sentiment_negative_ratios

    @pr_comment_sentiment_negative_ratio.setter
    def pr_comment_sentiment_negative_ratio(
        self, pr_comment_sentiment_negative_ratios: List[int]
    ) -> None:
        raise AttributeError(
            "Direct assignment to 'pr_comment_sentiment_negative_ratio' is not allowed. Use method addPRCommentSentimentNegativeRatio to modify this pr_comment_sentiment_negative property based on the requirement."
        )

    @property
    def smells(self) -> List[int]:
        return self._smells

    @smells.setter
    def smells(self, smells: List[List[str]]) -> None:
        raise AttributeError(
            "Direct assignment to 'smells' is not allowed. Use method addSmell to modify this property based on the requirement."
        )

    @property
    def author_count(self) -> List[int]:
        return self._author_counts

    @author_count.setter
    def author_count(self, author_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'author_count' is not allowed. Use method addAuthorCount to modify this property based on the requirement."
        )

    @property
    def sponsored_author_count(self) -> List[int]:
        return self._sponsored_author_counts

    @sponsored_author_count.setter
    def sponsored_author_count(self, sponsored_author_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'sponsored_author_count' is not allowed. Use method addSponsoredAuthorCount to modify this property based on the requirement."
        )

    @property
    def percentage_sponsored_author(self) -> List[int]:
        return self._percentage_sponsored_authors

    @percentage_sponsored_author.setter
    def percentage_sponsored_author(
        self, percentage_sponsored_authors: List[int]
    ) -> None:
        raise AttributeError(
            "Direct assignment to 'percentage_sponsored_author' is not allowed. Use method addPercentageSponsoredAuthor to modify this property based on the requirement."
        )

    @property
    def timezone_counts(self) -> List[int]:
        return self._timezone_counts

    @timezone_counts.setter
    def timezone_counts(self, timezone_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'timezone_count' is not allowed. Use method addTimeZoneCount to modify this property based on the requirement."
        )

    @property
    def metric_datas(self) -> List[int]:
        return self._metric_datas

    @metric_datas.setter
    def metric_datas(self, metric_datas: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'metric_data' is not allowed. Use method addMetricData to modify this property based on the requirement."
        )

    @property
    def first_commit_dates(self) -> List[str]:
        return self._first_commit_dates

    @first_commit_dates.setter
    def first_commit_dates(self, first_commit_dates: List[str]) -> None:
        raise AttributeError(
            "Direct assignment to 'first_commit_dates' is not allowed. Use method addFirstCommitDate to modify this property based on the requirement."
        )

    @property
    def last_commit_dates(self) -> List[str]:
        return self._last_commit_dates

    @last_commit_dates.setter
    def last_commit_dates(self, last_commit_dates: List[str]) -> None:
        raise AttributeError(
            "Direct assignment to 'last_commit_dates' is not allowed. Use method addLastCommitDate to modify this property based on the requirement."
        )

    @property
    def days_active(self) -> List[int]:
        return self._days_active

    @days_active.setter
    def days_active(self, days_active_count: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'days_active' is not allowed. Use method addDaysActive to modify this property based on the requirement."
        )

    @property
    def batch_dates(self) -> List[datetime]:
        return self._batch_dates

    @batch_dates.setter
    def batch_dates(self, batch_dates: List[datetime]) -> None:
        raise AttributeError(
            "Direct assignment to 'batch_dates' is not allowed. Use method setBatchDates  to modify this property based on the requirement."
        )

    @property
    def core_devs(self) -> List[datetime]:
        return self._core_devs

    @core_devs.setter
    def core_devs(self, core_devs: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'core_devs' is not allowed. Use method addCoreDev to modify this property based on the requirement."
        )

    def addCommitCount(self, batch_idx: int, commit_count: int) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and commit counts of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(commit_count, int):
            self.logger.error("Incorrect value type for commit count")
            raise ValueError(
                f"Incorrect value {commit_count} was passed for commit count. It is of type {type(commit_count)}. It should be an integer"
            )
        self._commit_count.insert(batch_idx, commit_count)
        return None

    def addBatchDates(self, batch_dates: List[datetime]) -> None:
        for batch_date in batch_dates:
            self._batch_dates.append(batch_date)
        self.logger.info("All values of Result are being reset")
        self._commit_count = []
        self._core_devs = []
        self._commit_count = []
        self._core_devs = []
        self._days_active = []
        self._first_commit_dates = []
        self._last_commit_dates = []
        self._author_counts = []
        self._sponsored_author_counts = []
        self._percentage_sponsored_authors = []
        self._timezone_counts = []
        self._metric_datas = []
        self._smells = []

        return None

    def addCoreDev(self, core_dev: str) -> None:
        if not isinstance(core_dev, str):
            self.logger.error("Incorrect value type for core devs")
            raise ValueError(
                f"Incorrect value for core dev is passed. The value is {core_dev} and it's type is {type(core_dev)}, but it should be string."
            )

        self._core_devs.append(core_dev)
        return None

    def addDaysActive(self, batch_idx: int, days_active: List[int]) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and days active count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(days_active, int):
            self.logger.error("Incorrect value type for days active")
            raise ValueError(
                f"Incorrect value {days_active} was passed for days active. It is of type {type(days_active)}. It should be an integer"
            )

        self._days_active.insert(batch_idx, days_active)
        return None

    def addFirstCommitDate(self, batch_idx: int, first_commit_date: datetime) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and first commit dates batch count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(first_commit_date, datetime):
            self.logger.error("Incorrect value type for first commit date")
            raise ValueError(
                f"Incorrect value {first_commit_date} was passed for first commit date. It is of type {type(first_commit_date)}. It should be of type datetime."
            )
        self._first_commit_dates.insert(
            batch_idx, "{:%Y-%m-%d}".format(first_commit_date)
        )
        return None

    def addLastCommitDate(self, batch_idx: int, last_commit_date: datetime) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and last commit dates batch count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(last_commit_date, datetime):
            self.logger.error("Incorrect value type for last commit date")
            raise ValueError(
                f"Incorrect value {last_commit_date} was passed for last commit date. It is of type {type(last_commit_date)}. It should be of type datetime."
            )
        self._last_commit_dates.insert(
            batch_idx, "{:%Y-%m-%d}".format(last_commit_date)
        )
        return None

    def addAuthorCount(self, batch_idx: int, author_count: int) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and author counts of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(author_count, int):
            self.logger.error("Incorrect value type for author count")
            raise ValueError(
                f"Incorrect value {author_count} was passed for author count. It is of type {type(author_count)}. It should be an integer"
            )
        self._author_counts.insert(batch_idx, author_count)
        return None

    def addSponsoredAuthorCount(
        self, batch_idx: int, sponsored_author_count: int
    ) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and sponsored_author counts of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(sponsored_author_count, int):
            self.logger.error("Incorrect value type for sponsored_author count")
            raise ValueError(
                f"Incorrect value {sponsored_author_count} was passed for sponsored_author count. It is of type {type(sponsored_author_count)}. It should be an integer"
            )

        self._sponsored_author_counts.insert(batch_idx, sponsored_author_count)
        return None

    def addPercentageSponsoredAuthor(
        self, batch_idx: int, percentage_sponsored_author: float
    ) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and percentage_sponsored_author of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(percentage_sponsored_author, float):
            self.logger.error("Incorrect value type for percentage_sponsored_author")
            raise ValueError(
                f"Incorrect value {percentage_sponsored_author} was passed for percentage_sponsored_author count. It is of type {type(percentage_sponsored_author)}. It should be an float"
            )

        self._percentage_sponsored_authors.insert(
            batch_idx, percentage_sponsored_author
        )
        return None

    def addTimeZoneCount(self, batch_idx: int, timezone_count: int) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and timezone_count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(timezone_count, int):
            self.logger.error("Incorrect value type for timezone_count")
            raise ValueError(
                f"Incorrect value {timezone_count} was passed for timezone_count. It is of type {type(timezone_count)}. It should be an integer"
            )

        self._timezone_counts.insert(batch_idx, timezone_count)
        return None

    def addMetricData(
        self, batch_idx: int, metric: str, count: int, mean: float, std_dev: float
    ) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and metric data of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif (
            not isinstance(metric, str)
            or not isinstance(count, int)
            or not isinstance(mean, float)
            or not (isinstance(std_dev, float) or std_dev is None)
        ):
            self.logger.error("Incorrect value type for metric data")
            raise ValueError(
                f"Incorrect arguments passed for addMetricData function. The expected value type and passed value type are as follows\nArgument\tExpected\tReceived\nmetric\tstr\t{type(metric)}\ncount\tint\t{type(count)}\nmean\tfloat\t{type(mean)}\nstd_dev\tfloat\t{type(std_dev)}"
            )
        if batch_idx >= len(self._metric_datas):
            self._metric_datas.insert(batch_idx, [("Metric", "Count", "Mean", "Stdev")])
        self._metric_datas[batch_idx].append((metric, count, mean, std_dev))
        return None

    def addPRCount(self, batch_idx: int, pr_count: int) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and pr count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(pr_count, int):
            self.logger.error("Incorrect value type for pr count")
            raise ValueError(
                f"Incorrect value {pr_count} was passed for pr_count. It is of type {type(pr_count)}. It should be an integer"
            )
        self._pr_counts.append(pr_count)
        return None

    def addSmell(self, batch_idx: int, smell: str) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and smells of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(smell, str):
            self.logger.error("Incorrect value type for smell")
            raise ValueError(
                f"Incorrect arguments passed for addSmell function. The expected value type is str but got {type(smell)}"
            )
        elif smell not in [
            "OSE",
            "BCE",
            "PDE",
            "SV",
            "OS",
            "SD",
            "RS",
            "TF",
            "UI",
            "TC",
        ]:
            self.logger.error("Incorrect smell type passed")
            raise ValueError(
                f"Incorrect smell type passed. It should be one of these {[
                    'OSE',
                    'BCE',
                    'PDE',
                    'SV',
                    'OS',
                    'SD',
                    'RS',
                    'TF',
                    'UI',
                    'TC',
                ]}"
            )
        if batch_idx >= len(self._smells):
            self._smells.insert(batch_idx, [])
        self._smells[batch_idx].append(smell)

    def getMetaResults(self) -> List[List[List[Any]]] | List[List[Any]]:
        result: List[List[List[Any]]] = []
        for idx in range(len(self._batch_dates)):
            result.append(
                [
                    ["CommitCount", self._commit_count[idx]],
                    ["DaysActive", self._days_active[idx]],
                    ["FirstCommitDate", self._first_commit_dates[idx]],
                    ["LastCommitDate", self._last_commit_dates[idx]],
                    ["AuthorCount", self._author_counts[idx]],
                    ["SponsoredAuthorCount", self._sponsored_author_counts[idx]],
                    [
                        "PercentageSponsoredAuthors",
                        self._percentage_sponsored_authors[idx],
                    ],
                    ["TimezoneCount", self._timezone_counts[idx]],
                ]
            )

        if len(self._batch_dates) == 1:
            return result[0]
        else:
            return result

    def getWebResult(self) -> Dict[str, Any]:
        if len(self._batch_dates) == 1:
            return dict(
                batch_date=self._batch_dates[0].strftime("%Y-%m-%d"),
                smell_results=self.smells[0],
                core_devs=self._core_devs,
                meta=self.getMetaResults(),
                metrics=self._metric_datas[0],
            )

    def addPRCommentCount(self, batch_idx: int, pr_comment_count: int) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and pr_comment count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(pr_comment_count, int):
            self.logger.error("Incorrect value type for pr_comment count")
            raise ValueError(
                f"Incorrect value {pr_comment_count} was passed for pr_comment_count. It is of type {type(pr_comment_count)}. It should be an integer"
            )
        self._pr_comment_counts.append(pr_comment_count)
        return None

    def addPRCommentSentimentPositiveCount(
        self, batch_idx: int, pr_comment_sentiment_positive_count: int
    ) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and pr_comment_sentiment_positive count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(pr_comment_sentiment_positive_count, int):
            self.logger.error(
                "Incorrect value type for pr_comment_sentiment_positive count"
            )
            raise ValueError(
                f"Incorrect value {pr_comment_sentiment_positive_count} was passed for pr_comment_sentiment_positive_count. It is of type {type(pr_comment_sentiment_positive_count)}. It should be an integer"
            )
        self._pr_comment_sentiment_positive_counts.append(
            pr_comment_sentiment_positive_count
        )
        return None

    def addPRCommentSentimentNegativeCount(
        self, batch_idx: int, pr_comment_sentiment_negative_count: int
    ) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and pr_comment_sentiment_negative count of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(pr_comment_sentiment_negative_count, int):
            self.logger.error(
                "Incorrect value type for pr_comment_sentiment_negative count"
            )
            raise ValueError(
                f"Incorrect value {pr_comment_sentiment_negative_count} was passed for pr_comment_sentiment_negative_count. It is of type {type(pr_comment_sentiment_negative_count)}. It should be an integer"
            )
        self._pr_comment_sentiment_negative_counts.append(
            pr_comment_sentiment_negative_count
        )
        return None

    def addPRCommentSentimentNegativeRatio(
        self, batch_idx: int, pr_comment_sentiment_negative_ratio: int
    ) -> None:
        if batch_idx >= len(self._batch_dates):
            self.logger.error(
                f"Mismatch between batch size of {len(self._batch_dates)} and pr_comment_sentiment_negative_ratio of {batch_idx + 1}"
            )
            raise ValueError(
                f"The index provided for the batch {batch_idx} is greater than length of batch dates {len(self._batch_dates)}!!"
            )
        elif not isinstance(pr_comment_sentiment_negative_ratio, int):
            self.logger.error(
                "Incorrect value type for pr_comment_sentiment_negative_ratio"
            )
            raise ValueError(
                f"Incorrect value {pr_comment_sentiment_negative_ratio} was passed for pr_comment_sentiment_negative_ratio. It is of type {type(pr_comment_sentiment_negative_ratio)}. It should be an integer"
            )
        self._pr_comment_sentiment_negative_ratios.append(
            pr_comment_sentiment_negative_ratio
        )
        return None
