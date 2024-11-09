from datetime import datetime
from typing import List
from unittest.mock import patch

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
@patch("logging.Logger")
def test_addCommitCountCorrect(
    mock_logger,
    batch_dates: List[datetime],
    commit_counts: List[int],
    expected_commit_count: List[int],
) -> None:

    mock_logger.info.return_value = "All values of Result are being reset"
    result = Result(logger=mock_logger)
    result.addBatchDates(batch_dates)
    for idx, commit_count in enumerate(commit_counts):
        result.addCommitCount(batch_idx=idx, commit_count=commit_count)
    mock_logger.info.assert_called_once_with("All values of Result are being reset")

    assert result.commit_count, expected_commit_count
