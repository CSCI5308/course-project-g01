import unittest
from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta

from MLbackend.src.graphqlAnalysis.prAnalysis import prRequest


class TestPRRequest(unittest.TestCase):

    @classmethod
    @patch("logging.Logger")
    def setUpClass(cls, mock_logger) -> None:
        cls.delta = relativedelta(months=+9999)
        cls.mock_logger = MagicMock()
        cls.mock_logger.return_value = cls.mock_logger

    @patch("MLbackend.src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_noPRsAvailable(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {"repository": None}
        batch_dates: List[datetime] = [datetime.now(timezone.utc)]
        result = prRequest(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batch_dates=batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(result, [[]])
        mock_runGraphqlRequest.assert_called_once()
        self.mock_logger.error.assert_called_once_with(
            "There are no PRs for this repository"
        )

        return None

    @patch("MLbackend.src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_prsAvailableNumberOfBatches(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {
            "repository": {
                "pullRequests": {
                    "page_info": {
                        "endCursor": "Y3Vyc29yOnYyOpHOBYEJRz==",
                        "hasNextPage": False,
                    },
                    "nodes": [
                        {
                            "number": 42,
                            "created_at": "2024-01-10T09:00:00Z",
                            "closedAt": "2024-01-12T12:30:00Z",
                            "participants": {
                                "nodes": [
                                    {"login": "contributor1"},
                                    {"login": "reviewer1"},
                                ]
                            },
                            "commits": {"totalCount": 5},
                            "comments": {
                                "nodes": [
                                    {"bodyText": "This looks great! Let's merge it."},
                                    {
                                        "bodyText": "Please address the requested changes."
                                    },
                                ]
                            },
                        }
                    ],
                }
            }
        }
        batch_dates: List[datetime] = [datetime.now(timezone.utc)]

        result = prRequest(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batch_dates=batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(len(result), 1)

        mock_runGraphqlRequest.assert_called_once()
        self.mock_logger.assert_not_called()

        return None

    @patch("MLbackend.src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_prsAvailableTwoOfBatches(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {
            "repository": {
                "pullRequests": {
                    "page_info": {
                        "endCursor": "Y3Vyc29yOnYyOpHOBYEJRz==",
                        "hasNextPage": False,
                    },
                    "nodes": [
                        {
                            "number": 42,
                            "created_at": "2024-09-22T09:00:00Z",
                            "closedAt": "2024-09-25T12:30:00Z",
                            "participants": {
                                "nodes": [
                                    {"login": "contributor1"},
                                    {"login": "reviewer1"},
                                ]
                            },
                            "commits": {"totalCount": 5},
                            "comments": {
                                "nodes": [
                                    {"bodyText": "This looks great! Let's merge it."},
                                    {
                                        "bodyText": "Please address the requested changes."
                                    },
                                ]
                            },
                        },
                        {
                            "number": 57,
                            "created_at": "2024-10-22T09:00:00Z",
                            "closedAt": None,
                            "participants": {
                                "nodes": [
                                    {"login": "contributor1"},
                                    {"login": "reviewer1"},
                                ]
                            },
                            "commits": {"totalCount": 5},
                            "comments": {
                                "nodes": [
                                    {"bodyText": "This looks great! Let's merge it."},
                                    {
                                        "bodyText": "Please address the requested changes."
                                    },
                                ]
                            },
                        },
                    ],
                }
            }
        }
        batch_dates: List[datetime] = [
            datetime.now(timezone.utc) - relativedelta(months=1, days=5),
            datetime.now(timezone.utc) - relativedelta(days=5),
        ]

        result = prRequest(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=relativedelta(months=+1),
            batch_dates=batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(len(result), 2)

        mock_runGraphqlRequest.assert_called_once()
        self.mock_logger.assert_not_called()

        return None


if __name__ == "__main__":
    unittest.main()
