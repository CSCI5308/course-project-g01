import unittest
from unittest.mock import patch, MagicMock
from src.graphqlAnalysis.prAnalysis import prRequest
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestPRRequest(unittest.TestCase):

    @classmethod
    @patch("logging.Logger")
    def setUpClass(cls, mock_logger) -> None:
        cls.delta = relativedelta(months=+9999)
        cls.batch_dates = [datetime.now()]
        cls.mock_logger = MagicMock()
        cls.mock_logger.return_value = cls.mock_logger

    @patch("src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_noReleaseAvailable(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {"repository": None}
        result = prRequest(
            pat="test_pat",
            owner="test_owner",
            name="test_name",
            delta=self.delta,
            batchDates=self.batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(result, [])
        mock_runGraphqlRequest.assert_called_once()
        self.mock_logger.error.assert_called_once_with(
            "There are no PRs for this repository"
        )

        return None


if __name__ == "__main__":
    unittest.main()
