import unittest
from unittest.mock import patch, MagicMock
from src.graphqlAnalysis.prAnalysis import prRequest
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


class TestPRRequest(unittest.TestCase):

    @classmethod
    @patch("logging.Logger")
    def setUpClass(cls, mock_logger) -> None:
        cls.delta = relativedelta(months=+9999)
        cls.batch_dates = [datetime.now(timezone.utc)]
        cls.mock_logger = MagicMock()
        cls.mock_logger.return_value = cls.mock_logger

    @patch("src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_noPRsAvailable(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {"repository": None}
        result = prRequest(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batchDates=self.batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(result, [[]])
        mock_runGraphqlRequest.assert_called_once()
        self.mock_logger.error.assert_called_once_with(
            "There are no PRs for this repository"
        )

        return None

    @patch("src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_prsAvailableNumberOfBatches(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {
            "repository": {
                "pullRequests": {
                    "pageInfo": {
                        "endCursor": "Y3Vyc29yOnYyOpHOBYEJRz==",
                        "hasNextPage": False,
                    },
                    "nodes": [
                        {
                            "number": 42,
                            "createdAt": "2024-01-10T09:00:00Z",
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

        result = prRequest(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batchDates=self.batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(len(result), 1)

        mock_runGraphqlRequest.assert_called_once()
        self.mock_logger.assert_not_called()

        return None


if __name__ == "__main__":
    unittest.main()
