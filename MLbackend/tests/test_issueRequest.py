import unittest
from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta

from MLbackend.src.graphql_analysis.issue_analysis import issue_request


class TestIssueRequest(unittest.TestCase):

    @classmethod
    @patch("logging.Logger")
    def setUpClass(cls, mock_logger) -> None:
        cls.delta = relativedelta(months=+9999)
        cls.mock_logger = MagicMock()
        cls.mock_logger.return_value = cls.mock_logger

    @patch("MLbackend.src.graphql_analysis.graphql_analysis_helper.run_graphql_request")
    def test_noIssuesAvailable(self, mock_run_graphql_request) -> None:
        mock_run_graphql_request.return_value = {"repository": None}
        batch_dates: List[datetime] = [datetime.now(timezone.utc)]
        result = issue_request(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batch_dates=batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(result, [[]])
        mock_run_graphql_request.assert_called_once()
        self.mock_logger.error.assert_called_once_with(
            "There are no Issues for this repository"
        )

        return None

    @patch("MLbackend.src.graphql_analysis.graphql_analysis_helper.run_graphql_request")
    def test_issuesAvailableNumberOfBatches(self, mock_run_graphql_request) -> None:
        # Generate the created_at date as today's date minus some days
        created_at_date = datetime.now() + timedelta(days=10)
        closed_at_date = datetime.now() + timedelta(days=15)
        created_at_iso = created_at_date.isoformat() + "Z"
        closed_at_iso = closed_at_date.isoformat() + "Z"
        mock_run_graphql_request.return_value = {
            "repository": {
                "issues": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "number": 1,
                            "createdAt": created_at_iso,
                            "closedAt": closed_at_iso,
                            "participants": {
                                "nodes": [{"login": "user1"}, {"login": "user2"}]
                            },
                            "comments": {
                                "nodes": [
                                    {"bodyText": "This is a comment on the issue."}
                                ]
                            },
                        }
                    ],
                }
            }
        }

        batch_dates: List[datetime] = [datetime.now(timezone.utc) - timedelta(days=5)]

        result = issue_request(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batch_dates=batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(len(result), 1)

        mock_run_graphql_request.assert_called_once()
        self.mock_logger.assert_not_called()

        return None

    @patch("MLbackend.src.graphql_analysis.graphql_analysis_helper.run_graphql_request")
    def test_issuesAvailableTwoOfBatches(self, mock_run_graphql_request) -> None:
        created_at_date = datetime.now() - relativedelta(months=1, days=10)
        closed_at_date = datetime.now() - relativedelta(months=1, days=15)
        mock_run_graphql_request.return_value = {
            "repository": {
                "issues": {
                    "pageInfo": {
                        "endCursor": "Y3Vyc29yOnYyOpHOBYEJRz==",
                        "hasNextPage": False,
                    },
                    "nodes": [
                        {
                            "number": 57,
                            "createdAt": (
                                created_at_date + relativedelta(months=1, days=10)
                            ).isoformat()
                            + "Z",
                            "closedAt": None,
                            "participants": {
                                "nodes": [{"login": "user1"}, {"login": "user2"}]
                            },
                            "comments": {
                                "nodes": [
                                    {"bodyText": "This is a comment on the issue."}
                                ]
                            },
                        },
                        {
                            "number": 1,
                            "createdAt": (
                                created_at_date + relativedelta(days=10)
                            ).isoformat()
                            + "Z",
                            "closedAt": closed_at_date.isoformat() + "Z",
                            "participants": {
                                "nodes": [{"login": "user1"}, {"login": "user2"}]
                            },
                            "comments": {
                                "nodes": [
                                    {"bodyText": "This is a comment on the issue."}
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

        result = issue_request(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=relativedelta(months=+1),
            batch_dates=batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(len(result), 2)

        mock_run_graphql_request.assert_called_once()
        self.mock_logger.assert_not_called()

        return None


if __name__ == "__main__":
    unittest.main()
