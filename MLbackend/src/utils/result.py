from datetime import datetime
from typing import List


class Result:

    def __init__(self) -> None:

        self._batch_dates: List[datetime] = []
        self._commit_count: List[int] = []

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
    def batch_dates(self) -> List[datetime]:
        return self.batch_dates

    @batch_dates.setter
    def batch_dates(self, commit_counts: List[int]) -> None:
        raise AttributeError(
            "Direct assignment to 'batch_dates' is not allowed. Use method setBatchDates  to modify this property based on the requirement."
        )

    def addCommitCount(self, batch_idx: int, commit_count: int) -> None:

        self._commit_count.insert(batch_idx, commit_count)
        return None

    def addBatchDates(self, batch_dates: List[datetime]) -> None:
        self._batch_dates = batch_dates
        self._commit_count = []
        return None
