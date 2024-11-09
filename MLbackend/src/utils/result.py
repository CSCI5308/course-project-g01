from datetime import datetime
from logging import Logger
from typing import List

from dateutil.relativedelta import relativedelta


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
        self.logger: Logger = logger

        return None

    @property
    def commit_count(self) -> List[int]:
        return self._commit_count

    @commit_count.setter
    def commit_count(self, commit_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'commit_count' is not allowed. Use method addCommitCount to modify this property based on the requirement."
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
        self._batch_dates = batch_dates
        self.logger.info("All values of Result are being reset")
        self._commit_count = []
        self._core_devs = []
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
        self._sponsored_author_counts.insert(batch_idx, sponsored_author_count)
        return None
