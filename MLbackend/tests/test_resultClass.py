from datetime import datetime
from logging import Logger
from typing import Any, List
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta

from MLbackend.src.utils.result import Result


@pytest.fixture
@patch("logging.Logger")
def logger_instance(mock_logger) -> Logger:
    return mock_logger


@pytest.fixture
def result_instance(logger_instance: Logger) -> Result:
    return Result(logger=logger_instance)


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
    result_instance,
    logger_instance,
    batch_dates: List[datetime],
    commit_counts: List[int],
    expected_commit_count: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, commit_count in enumerate(commit_counts):
        result_instance.addCommitCount(batch_idx=idx, commit_count=commit_count)

    assert result_instance.commit_count, expected_commit_count
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


# @pytest.mark.parametrize(
#     "batch_dates, commit_counts, expected_commit_count",
#     [
#         (
#             [datetime.now()],
#             [5, 5],
#             [
#                 5,
#             ],
#         ),
#         ([datetime.now(), datetime.now() - relativedelta(days=5)], [5, "a"], None),
#         (
#             [datetime.now(), datetime.now(), datetime.now() - relativedelta(days=5)],
#             [5, "a"],
#             None,
#         ),
#     ],
# )
@pytest.mark.parametrize(
    "batch_dates, commit_counts",
    [([datetime.now()], [5, 5]), ([datetime.now(), datetime.now()], [5, 1, 6])],
)
def test_addCommitCountFailsDueToLessBatchSize(
    result_instance,
    logger_instance,
    batch_dates: List[datetime],
    commit_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and commit counts of {len(commit_counts)}"
    result_instance.addBatchDates(batch_dates)
    idx: int = 0
    for idx in range(len(commit_counts) - 1):
        result_instance.addCommitCount(batch_idx=idx, commit_count=commit_counts[idx])

    with pytest.raises(ValueError):
        result_instance.addCommitCount(batch_idx=idx, commit_count=commit_counts[-1])

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and commit counts of {len(commit_counts)}"
    )

    return None
