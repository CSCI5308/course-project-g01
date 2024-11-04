import unittest
from typing import List
from unittest.mock import patch, MagicMock
from src.graphqlAnalysis.issueAnalysis import issueRequest
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


class TestIssueRequest(unittest.TestCase):

    @classmethod
    @patch("logging.Logger")
    def setUpClass(cls, mock_logger) -> None:
        cls.delta = relativedelta(months=+9999)
        cls.mock_logger = MagicMock()
        cls.mock_logger.return_value = cls.mock_logger

    @patch("src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_noIssuesAvailable(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {"repository": None}
        batch_dates: List[datetime] = [datetime.now(timezone.utc)]
        result = issueRequest(
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
            "There are no Issues for this repository"
        )

        return None


if __name__ == "__main__":
    unittest.main()
