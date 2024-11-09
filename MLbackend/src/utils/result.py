from datetime import datetime
from logging import Logger
from typing import List


class Result:

    def __init__(self, logger: Logger) -> None:

        self._batch_dates: List[datetime] = []
        self._commit_count: List[int] = []
        self._core_devs: List[str] = []
        self._days_active: List[int] = []
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
        self._days_active.insert(batch_idx, days_active)
        return None
