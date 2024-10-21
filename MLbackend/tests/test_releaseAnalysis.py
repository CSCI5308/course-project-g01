import unittest
from unittest.mock import patch, MagicMock
from src.graphqlAnalysis.releaseAnalysis import releaseRequest
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestReleaseAnalysis(unittest.TestCase):

    @classmethod
    @patch("src.configuration.Configuration")
    def setUpClass(cls, mock_configuration) -> None:
        cls.mock_config_instance = MagicMock()

        # Set return values for the properties you need
        cls.mock_config_instance.repositoryUrl = "test_url"
        cls.mock_config_instance.pat = "test_pat"
        cls.mock_config_instance.outputPath = Path()
        cls.mock_config_instance.sentiStrengthPath = Path()
        cls.mock_config_instance.batchMonths = 9999
        cls.mock_config_instance.maxDistance = 0
        cls.mock_config_instance.startDate = datetime.now()
        cls.mock_config_instance.googleKey = None
        cls.delta = relativedelta(months=+cls.mock_config_instance.batchMonths)
        cls.batch_dates = [datetime.now()]

    @patch("src.graphqlAnalysis.graphqlAnalysisHelper.runGraphqlRequest")
    def test_noReleaseAvailable(self, mock_runGraphqlRequest) -> None:
        mock_runGraphqlRequest.return_value = {"repository": None}
        result = releaseRequest(
            config=self.mock_config_instance,
            delta=self.delta,
            batchDates=self.batch_dates,
            logger=None,
        )

        self.assertEqual(result, [])
        mock_runGraphqlRequest.assert_called_once()

        return None


if __name__ == "__main__":
    unittest.main()
