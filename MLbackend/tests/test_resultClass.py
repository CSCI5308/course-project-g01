from datetime import datetime
from logging import Logger
from typing import Any, List, Tuple
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

    assert result_instance.commit_count == expected_commit_count
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

    assert result_instance.core_devs == expected_core_devs
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

    assert result_instance.days_active == expected_days_active
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


@pytest.mark.parametrize(
    "batch_dates, days_active",
    [
        ([datetime.now(), datetime.now()], [5, "a"]),
        ([datetime.now(), datetime.now(), datetime.now()], [5, "b", 6]),
    ],
)
def test_addDaysActiveFailsDueToIncorrectDaysActiveValueType(
    result_instance,
    batch_dates: List[datetime],
    days_active: List[Any],
) -> None:

    result_instance.logger.error.return_value = "Incorrect value type for days active"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, days_active in enumerate(days_active):
            result_instance.addDaysActive(batch_idx=idx, days_active=days_active)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for days active"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, first_commit_dates, expected_first_commit_dates",
    [
        (
            [datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
            ],
            [
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=10)),
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
            ],
            [
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=10)),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
            ],
        ),
        (
            [
                datetime.now(),
                datetime.now() - relativedelta(days=5),
                datetime.now() - relativedelta(days=10),
            ],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
                datetime.now() - relativedelta(days=25),
            ],
            [
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=10)),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=25)),
            ],
        ),
    ],
)
def test_addFirstCommitDateCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    first_commit_dates: List[int],
    expected_first_commit_dates: List[str],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, first_commit_date in enumerate(first_commit_dates):
        result_instance.addFirstCommitDate(
            batch_idx=idx, first_commit_date=first_commit_date
        )

    assert result_instance.first_commit_dates == expected_first_commit_dates
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, first_commit_dates",
    [
        (
            [datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
                datetime.now() - relativedelta(days=18),
            ],
        ),
    ],
)
def test_addFirstCommitDateFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    first_commit_dates: List[datetime],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and first commit dates batch count of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, first_commit_date in enumerate(first_commit_dates):
            result_instance.addFirstCommitDate(
                batch_idx=idx, first_commit_date=first_commit_date
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and first commit dates batch count of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, first_commit_dates",
    [
        (
            [datetime.now(), datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5), datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
                datetime.now() - relativedelta(days=18),
            ],
        ),
    ],
)
def test_addFirstCommitDateFailsDueToIncorrectDaysActiveValueType(
    result_instance,
    batch_dates: List[datetime],
    first_commit_dates: List[datetime],
) -> None:

    result_instance.logger.error.return_value = (
        "Incorrect value type for first commit date"
    )
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, first_commit_date in enumerate(first_commit_dates):
            result_instance.addFirstCommitDate(
                batch_idx=idx, first_commit_date=first_commit_date
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for first commit date"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, last_commit_dates, expected_last_commit_dates",
    [
        (
            [datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
            ],
            [
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=10)),
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
            ],
            [
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=10)),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
            ],
        ),
        (
            [
                datetime.now(),
                datetime.now() - relativedelta(days=5),
                datetime.now() - relativedelta(days=10),
            ],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
                datetime.now() - relativedelta(days=25),
            ],
            [
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=10)),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=25)),
            ],
        ),
    ],
)
def test_addLastCommitDateCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    last_commit_dates: List[int],
    expected_last_commit_dates: List[str],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, last_commit_date in enumerate(last_commit_dates):
        result_instance.addLastCommitDate(
            batch_idx=idx, last_commit_date=last_commit_date
        )

    assert result_instance.last_commit_dates == expected_last_commit_dates
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, last_commit_dates",
    [
        (
            [datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                datetime.now() - relativedelta(days=10),
                datetime.now() - relativedelta(days=15),
                datetime.now() - relativedelta(days=18),
            ],
        ),
    ],
)
def test_addLastCommitDateFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    last_commit_dates: List[datetime],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and last commit dates batch count of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, last_commit_date in enumerate(last_commit_dates):
            result_instance.addLastCommitDate(
                batch_idx=idx, last_commit_date=last_commit_date
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and last commit dates batch count of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, last_commit_dates",
    [
        (
            [datetime.now(), datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5), datetime.now()],
            [
                datetime.now() - relativedelta(days=10),
                "{:%Y-%m-%d}".format(datetime.now() - relativedelta(days=15)),
                datetime.now() - relativedelta(days=18),
            ],
        ),
    ],
)
def test_addLastCommitDateFailsDueToIncorrectDaysActiveValueType(
    result_instance,
    batch_dates: List[datetime],
    last_commit_dates: List[datetime],
) -> None:

    result_instance.logger.error.return_value = (
        "Incorrect value type for last commit date"
    )
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, last_commit_date in enumerate(last_commit_dates):
            result_instance.addLastCommitDate(
                batch_idx=idx, last_commit_date=last_commit_date
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for last commit date"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, author_counts, expected_author_count",
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
def test_addAuthorCountCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    author_counts: List[int],
    expected_author_count: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, author_count in enumerate(author_counts):
        result_instance.addAuthorCount(batch_idx=idx, author_count=author_count)

    assert result_instance.author_count == expected_author_count
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, author_counts",
    [([datetime.now()], [5, 5]), ([datetime.now(), datetime.now()], [5, 1, 6])],
)
def test_addAuthorCountFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    author_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and author counts of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, author_count in enumerate(author_counts):
            result_instance.addAuthorCount(batch_idx=idx, author_count=author_count)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and author counts of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, author_counts",
    [
        ([datetime.now(), datetime.now()], [5, "a"]),
        ([datetime.now(), datetime.now(), datetime.now()], [5, "b", 6]),
    ],
)
def test_addAuthorCountFailsDueToIncorrectAuthorValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    author_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = "Incorrect value type for author count"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, author_count in enumerate(author_counts):
            result_instance.addAuthorCount(batch_idx=idx, author_count=author_count)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for author count"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, sponsored_author_counts, expected_sponsored_author_count",
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
def test_addSponsoredAuthorCountCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    sponsored_author_counts: List[int],
    expected_sponsored_author_count: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, sponsored_author_count in enumerate(sponsored_author_counts):
        result_instance.addSponsoredAuthorCount(
            batch_idx=idx, sponsored_author_count=sponsored_author_count
        )

    assert result_instance.sponsored_author_count == expected_sponsored_author_count
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, sponsored_author_counts",
    [([datetime.now()], [5, 5]), ([datetime.now(), datetime.now()], [5, 1, 6])],
)
def test_addSponsoredAuthorCountFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    sponsored_author_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and sponsored_author counts of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, sponsored_author_count in enumerate(sponsored_author_counts):
            result_instance.addSponsoredAuthorCount(
                batch_idx=idx, sponsored_author_count=sponsored_author_count
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and sponsored_author counts of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, sponsored_author_counts",
    [
        ([datetime.now(), datetime.now()], [5, "a"]),
        ([datetime.now(), datetime.now(), datetime.now()], [5, "b", 6]),
    ],
)
def test_addSponsoredAuthorCountFailsDueToIncorrectAuthorValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    sponsored_author_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = (
        "Incorrect value type for sponsored_author count"
    )
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, sponsored_author_count in enumerate(sponsored_author_counts):
            result_instance.addSponsoredAuthorCount(
                batch_idx=idx, sponsored_author_count=sponsored_author_count
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for sponsored_author count"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, percentage_sponsored_authors, expected_percentage_sponsored_author",
    [
        (
            [datetime.now()],
            [
                5.,
            ],
            [
                5.,
            ],
        ),
        ([datetime.now(), datetime.now() - relativedelta(days=5)], [5., 10.], [5., 10.]),
        (
            [datetime.now(), datetime.now(), datetime.now() - relativedelta(days=5)],
            [5., 10., 15.],
            [5., 10., 15.],
        ),
    ],
)
def test_addPercentageSponsoredAuthorCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    percentage_sponsored_authors: List[int],
    expected_percentage_sponsored_author: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, percentage_sponsored_author in enumerate(percentage_sponsored_authors):
        result_instance.addPercentageSponsoredAuthor(
            batch_idx=idx, percentage_sponsored_author=percentage_sponsored_author
        )

    assert (
        result_instance.percentage_sponsored_author
        == expected_percentage_sponsored_author
    )
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, percentage_sponsored_authors",
    [([datetime.now()], [5., 5.]), ([datetime.now(), datetime.now()], [5., 1., 6.])],
)
def test_addPercentageSponsoredAuthorFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    percentage_sponsored_authors: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and percentage_sponsored_author of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, percentage_sponsored_author in enumerate(percentage_sponsored_authors):
            result_instance.addPercentageSponsoredAuthor(
                batch_idx=idx, percentage_sponsored_author=percentage_sponsored_author
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and percentage_sponsored_author of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, percentage_sponsored_authors",
    [
        ([datetime.now(), datetime.now()], [5., "a"]),
        ([datetime.now(), datetime.now(), datetime.now()], [5., "b", 6.]),
    ],
)
def test_addPercentageSponsoredAuthorFailsDueToIncorrectAuthorValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    percentage_sponsored_authors: List[Any],
) -> None:

    result_instance.logger.error.return_value = (
        "Incorrect value type for percentage_sponsored_author"
    )
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, percentage_sponsored_author in enumerate(percentage_sponsored_authors):
            result_instance.addPercentageSponsoredAuthor(
                batch_idx=idx, percentage_sponsored_author=percentage_sponsored_author
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for percentage_sponsored_author"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, timezone_counts, expected_timezone_count",
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
def test_addTimeZoneCountCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    timezone_counts: List[int],
    expected_timezone_count: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, timezone_count in enumerate(timezone_counts):
        result_instance.addTimeZoneCount(batch_idx=idx, timezone_count=timezone_count)

    assert result_instance.timezone_counts == expected_timezone_count
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, timezone_counts",
    [([datetime.now()], [5, 5]), ([datetime.now(), datetime.now()], [5, 1, 6])],
)
def test_addTimeZoneCountFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    timezone_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and timezone_count of {len(batch_dates) + 1}"
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, timezone_count in enumerate(timezone_counts):
            result_instance.addTimeZoneCount(
                batch_idx=idx, timezone_count=timezone_count
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and timezone_count of {len(batch_dates) + 1}"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, timezone_counts",
    [
        ([datetime.now(), datetime.now()], [5, "a"]),
        ([datetime.now(), datetime.now(), datetime.now()], [5, "b", 6]),
    ],
)
def test_addTimeZoneCountFailsDueToIncorrectAuthorValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    timezone_counts: List[Any],
) -> None:

    result_instance.logger.error.return_value = (
        "Incorrect value type for timezone_count"
    )
    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)

    with pytest.raises(ValueError):
        for idx, timezone_count in enumerate(timezone_counts):
            result_instance.addTimeZoneCount(
                batch_idx=idx, timezone_count=timezone_count
            )

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for timezone_count"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, metric_data, expected_metric_data",
    [
        (
            [datetime.now()],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                ]
            ],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                ]
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ]
            ],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ]
            ]
        ),
        (
            [datetime.now(), datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentNegative", 2, -1.5, 0.707),
                ]
            ],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentNegative", 2, -1.5, 0.707),
                ]
            ]
        ),
    ],
)
def test_addMetricDataCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    metric_data: List[int],
    expected_metric_data: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, metric_data in enumerate(metric_data):
        for (metric, count, mean, std_dev) in metric_data:
            result_instance.addMetricData(batch_idx=idx, metric=metric, count=count, mean=mean, std_dev=std_dev)

    assert result_instance.metric_datas == expected_metric_data
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, metric_data, expected_metric_data",
    [
        (
            [datetime.now()],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, None),
                ]
            ],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, None),
                ]
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, None),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, None),
                ]
            ],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, None),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, None),
                ]
            ]
        ),
    ],
)
def test_addMetricDataNoneStdDev(
    result_instance: Result,
    batch_dates: List[datetime],
    metric_data: List[int],
    expected_metric_data: List[int],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, metric_data in enumerate(metric_data):
        for (metric, count, mean, std_dev) in metric_data:
            result_instance.addMetricData(batch_idx=idx, metric=metric, count=count, mean=mean, std_dev=std_dev)

    assert result_instance.metric_datas == expected_metric_data
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, metric_data",
    [
        (
            [datetime.now()],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                ]
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ],
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ]
            ]
        ),
    ],
)
def test_addMetricDataFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    metric_data: List[Tuple[str, int, float, float]],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and metric data of {len(batch_dates) + 1}"
    result_instance.addBatchDates(batch_dates)
    with pytest.raises(ValueError):
        for idx, metric_data in enumerate(metric_data):
            for (metric, count, mean, std_dev) in metric_data:
                result_instance.addMetricData(batch_idx=idx, metric=metric, count=count, mean=mean, std_dev=std_dev)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and metric data of {len(batch_dates) + 1}"
    )
    return None


@pytest.mark.parametrize(
    "batch_dates, metric_data",
    [
        (
            [datetime.now()],
            [
                [
                    (53, 2, 12.5, 10.61),
                ],
            ],
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", "55", 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ],
            ]
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, "1.6", 3.05),
                ],
                [
                    ("AuthorActiveDays", "55", 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ],
            ]
        ),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [
                [
                    ("AuthorActiveDays", 2, 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, 0.707),
                    ("CommitMessageSentiment", 5, 1.6, 3.05),
                ],
                [
                    ("AuthorActiveDays", "55", 12.5, 10.61),
                    ("AuthorCommitCount", 5, 2.5, "0.707"),
                    ("CommitMessageSentimentPositive", 3, 3.67, 1.53),
                ],
            ]
        ),
    ],
)
def test_addMetricDataFailsDueToIncorrectAuthorValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    metric_data: List[Tuple[str, int, float, float]],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.logger.error.return_value = "Incorrect value type for metric data"
    result_instance.addBatchDates(batch_dates)
    with pytest.raises(ValueError):
        for idx, metric_data in enumerate(metric_data):
            for (metric, count, mean, std_dev) in metric_data:
                result_instance.addMetricData(batch_idx=idx, metric=metric, count=count, mean=mean, std_dev=std_dev)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        "Incorrect value type for metric data"
    )
    return None


@pytest.mark.parametrize(
    "batch_dates, smells, expected_smells",
    [
        ([datetime.now(),], [["OSE", "BCE"]], [["OSE", "BCE"]],),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [["OSE", "BCE"], ["PDE",]],
            [["OSE", "BCE"], ["PDE",]],
        ),
        (
            [datetime.now(), datetime.now(), datetime.now() - relativedelta(days=5)],
            [["OSE", "BCE"], ["PDE",], ["RS", "TF"]],
            [["OSE", "BCE"], ["PDE",], ["RS", "TF"]],
        ),
    ],
)
def test_addSmellCorrect(
    result_instance: Result,
    batch_dates: List[datetime],
    smells: List[List[str]],
    expected_smells: List[List[str]],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.addBatchDates(batch_dates)
    for idx, smell in enumerate(smells):
        for detected_smell in smell:
            result_instance.addSmell(batch_idx=idx, smell=detected_smell)

    assert result_instance.smells == expected_smells
    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )

    return None


@pytest.mark.parametrize(
    "batch_dates, smells",
    [
        ([datetime.now(),], [["OSE", "BCE"], ["PDE",]]),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [["OSE", "BCE"], ["PDE",], ["RS", "TF"]],
        ),
    ],
)
def test_addSmellFailsDueToLessBatchSize(
    result_instance: Result,
    batch_dates: List[datetime],
    smells: List[List[str]],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.logger.error.return_value = f"Mismatch between batch size of {len(batch_dates)} and smells of {len(batch_dates) + 1}"
    result_instance.addBatchDates(batch_dates)
    with pytest.raises(ValueError):
        for idx, smell in enumerate(smells):
            for detected_smell in smell:
                result_instance.addSmell(batch_idx=idx, smell=detected_smell)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
        f"Mismatch between batch size of {len(batch_dates)} and smells of {len(batch_dates) + 1}"
    )
    return None


@pytest.mark.parametrize(
    "batch_dates, smells",
    [
        ([datetime.now(),], [["OSE", 58],]),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [["OSE", "BCE"], [56,]],
        ),
    ],
)
def test_addSmellFailsDueToIncorrectSmellValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    smells: List[List[str]],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.logger.error.return_value = "Incorrect value type for smell"
    result_instance.addBatchDates(batch_dates)
    with pytest.raises(ValueError):
        for idx, smell in enumerate(smells):
            for detected_smell in smell:
                result_instance.addSmell(batch_idx=idx, smell=detected_smell)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
         "Incorrect value type for smell"
    )
    return None


@pytest.mark.parametrize(
    "batch_dates, smells",
    [
        ([datetime.now(),], [["OSE", "MNP"],]),
        (
            [datetime.now(), datetime.now() - relativedelta(days=5)],
            [["OSE", "BCE"], ["XYZ",]],
        ),
    ],
)
def test_addSmellFailsDueToIncorrectAuthorValueType(
    result_instance: Result,
    batch_dates: List[datetime],
    smells: List[List[str]],
) -> None:

    result_instance.logger.info.return_value = "All values of Result are being reset"
    result_instance.logger.error.return_value = "Incorrect smell type passed"
    result_instance.addBatchDates(batch_dates)
    with pytest.raises(ValueError):
        for idx, smell in enumerate(smells):
            for detected_smell in smell:
                result_instance.addSmell(batch_idx=idx, smell=detected_smell)

    result_instance.logger.info.assert_called_once_with(
        "All values of Result are being reset"
    )
    result_instance.logger.error.assert_called_once_with(
         "Incorrect smell type passed"
    )
    return None
