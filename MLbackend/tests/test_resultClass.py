from datetime import datetime
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from MLbackend.src.utils.result import Result


@pytest.mark.parametrize(
    "batch_dates, commit_counts, expected_commit_count",
    [
        (
            [datetime.now()],
            [
                5,
            ],
            [
                5,
            ],
        ),
        ([datetime.now(), datetime.now() - relativedelta(days=5)], [5, 10], [5, 10]),
        (
            [datetime.now(), datetime.now(), datetime.now() - relativedelta(days=5)],
            [5, 10, 15],
            [5, 10, 15],
        ),
    ],
)
def test_addCommitCountCorrect(
    batch_dates: List[datetime],
    commit_counts: List[int],
    expected_commit_count: List[int],
) -> None:

    result = Result()
    result.addBatchDates(batch_dates)
    for idx, commit_count in enumerate(commit_counts):
        result.addCommitCount(batch_idx=idx, commit_count=commit_count)

    assert result.commit_count, expected_commit_count
