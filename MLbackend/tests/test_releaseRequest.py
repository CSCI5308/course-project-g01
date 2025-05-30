import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta

from MLbackend.src.graphql_analysis.release_analysis import release_request


class TestReleaseRequest(unittest.TestCase):

    @classmethod
    @patch("MLbackend.src.configuration.Configuration")
    @patch("logging.Logger")
    def setUpClass(cls, mock_configuration, mock_logger) -> None:
        cls.mock_config_instance = MagicMock()

        # Set return values for the properties you need
        cls.mock_config_instance.repositoryUrl = "test_url"
        cls.mock_config_instance.pat = "test_pat"
        cls.mock_config_instance.outputPath = Path()
        cls.mock_config_instance.sentiStrengthPath = Path()
        cls.mock_config_instance.batchMonths = 9999
        cls.mock_config_instance.maxDistance = 0
        cls.mock_config_instance.start_date = datetime.now()
        cls.mock_config_instance.googleKey = None
        cls.delta = relativedelta(months=+cls.mock_config_instance.batchMonths)
        cls.batch_dates = [datetime.now()]
        cls.mock_logger = MagicMock()
        cls.mock_logger.return_value = cls.mock_logger

    @patch("MLbackend.src.graphql_analysis.graphql_analysis_helper.run_graphql_request")
    def test_noReleaseAvailable(self, mock_run_graphql_request) -> None:
        mock_run_graphql_request.return_value = {"repository": None}
        result = release_request(
            config=self.mock_config_instance,
            delta=self.delta,
            batch_dates=self.batch_dates,
            logger=self.mock_logger,
        )

        self.assertEqual(result, [])
        mock_run_graphql_request.assert_called_once()
        self.mock_logger.error.assert_called_once_with(
            "There are no releases for this repository"
        )

        return None

    @patch("MLbackend.src.graphql_analysis.graphql_analysis_helper.run_graphql_request")
    def test_releaseAvailableNumberOfBatches(self, mock_run_graphql_request) -> None:
        mock_run_graphql_request.return_value = {
            "repository": {
                "releases": {
                    "totalCount": 1,
                    "nodes": [
                        {
                            "author": {"login": "sampleAuthor"},
                            "createdAt": "2024-01-15T12:00:00Z",
                            "name": "v1.0.0",
                        }
                    ],
                    "pageInfo": {
                        "endCursor": "Y3Vyc29yOnYyOpHOBYEJRz==",
                        "hasNextPage": False,
                    },
                }
            }
        }

        result = release_request(
            config=self.mock_config_instance,
            delta=self.delta,
            batch_dates=self.batch_dates,
            logger=self.mock_logger,
        )
        self.assertEqual(len(result), 1)

        mock_run_graphql_request.assert_called_once()
        self.mock_logger.assert_not_called()

        return None

    @patch("MLbackend.src.graphql_analysis.graphql_analysis_helper.run_graphql_request")
    def test_releaseAvailableNumberOfItemInBatch(self, mock_run_graphql_request) -> None:
        mock_run_graphql_request.return_value = {
            "repository": {
                "releases": {
                    "totalCount": 1,
                    "nodes": [
                        {
                            "author": {"login": "sampleAuthor"},
                            "createdAt": "2024-01-15T12:00:00Z",
                            "name": "v1.0.0",
                        }
                    ],
                    "pageInfo": {
                        "endCursor": "Y3Vyc29yOnYyOpHOBYEJRz==",
                        "hasNextPage": False,
                    },
                }
            }
        }

        result = release_request(
            config=self.mock_config_instance,
            delta=self.delta,
            batch_dates=self.batch_dates,
            logger=self.mock_logger,
        )
        self.assertEqual(len(result[0]["releases"]), 1)

        mock_run_graphql_request.assert_called_once()
        self.mock_logger.assert_not_called()

        return None


if __name__ == "__main__":
    unittest.main()
