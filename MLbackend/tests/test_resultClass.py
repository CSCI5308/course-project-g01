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
    result_instance: Result,
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


@pytest.mark.parametrize(
    "batch_dates, commit_counts",
    [([datetime.now()], [5, 5]), ([datetime.now(), datetime.now()], [5, 1, 6])],
)
def test_addCommitCountFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    commit_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and commit counts of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, commit_count in enumerate(commit_counts):
            result_instance.addCommitCount(batch_idx=idx, commit_count=commit_count)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and commit counts of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, commit_counts",
    [
        ([datetime.now(), datetime.now()], [5, "a"]),
        ([datetime.now(), datetime.now(), datetime.now()], [5, "b", 6]),
    ],
)
def test_addCommitCountFailsDueToIncorrectCommitValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    commit_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = "Incorrect value type for commit count"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, commit_count in enumerate(commit_counts):
            result_instance.addCommitCount(batch_idx=idx, commit_count=commit_count)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for commit count"
    )

    return None


@pytest.mark.parametrize(
    "core_devs, expected_core_devs",
    [
        (["CoreDev1", "CoreDev2"], ["CoreDev1", "CoreDev2"]),
        (["CoreDev1", "CoreDev2", "CoreDev3"], ["CoreDev1", "CoreDev2", "CoreDev3"]),
        (["CoreDev1"], ["CoreDev1"]),
    ],
)
def test_addCoreDevCorrect(
    result_instance: Result,
    core_devs: List[str],
    expected_core_devs: List[str],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    batch_dates: List[datetime] = [datetime.now()]
    result_instance.addBatchDates(batch_dates)

    for core_dev in core_devs:
        result_instance.addCoreDev(core_dev)

    assert result_instance.core_devs, expected_core_devs
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "core_devs",
    [
        (["CoreDev1", 563],),
        (["CoreDev1", 255, "CoreDev3"],),
        ([635],),
    ],
)
def test_addCoreDevIncorrectValueError(
    result_instance: Result,
    core_devs: List[str],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.logger.error.return_value = "Incorrect value type for core devs"
    batch_dates: List[datetime] = [datetime.now()]
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for core_dev in core_devs:
            result_instance.addCoreDev(core_dev)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for core devs"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, days_active, expected_days_active",
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
def test_addDaysActiveCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    days_active: List[int],
    expected_days_active: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, days_active in enumerate(days_active):
        result_instance.addDaysActive(batch_idx=idx, days_active=days_active)

    assert result_instance.days_active, expected_days_active
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, days_active",
    [([datetime.now()], [5, 5]), ([datetime.now(), datetime.now()], [5, 1, 6])],
)
def test_addDaysActiveFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    days_active: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and days active count of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, days_active in enumerate(days_active):
            result_instance.addDaysActive(batch_idx=idx, days_active=days_active)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and days active count of {len(batch_dates) + 1}"
    )

    return None
