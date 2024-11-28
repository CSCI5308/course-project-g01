
import unittest
from unittest.mock import MagicMock, patch, mock_open
from logging import Logger
import os
import csv
from  MLbackend.src.stats_analysis import output_statistics


def mock_calculate_stats(data, logger):
    return {
        "count": len(data),
        "mean": sum(data) / len(data) if data else 0,
        "stdev": (
            (sum((x - sum(data) / len(data)) ** 2 for x in data) / len(data)) ** 0.5
            if data
            else 0
        ),
    }


class TestOutputStatistics(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=Logger)
        self.output_dir = "mock_output_dir"
        os.makedirs(self.output_dir, exist_ok=True)

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.writer")
    @patch(
        "MLbackend.src.statsAnalysis.calculateStats", side_effect=mock_calculate_stats
    )
    def test_output_statistics_with_data(
        self, mock_calculate_stats, mock_csv_writer, mock_open
    ):
        data = [10, 20, 30]
        metric = "test_metric"

        metric, count, mean, stdev = output_statistics(1, data, metric, self.output_dir, self.mock_logger)

        # Assertions
        self.assertEqual(metric, "test_metric")
        self.assertEqual(count, 3)
        self.assertEqual(mean, "20.0000")
        self.assertNotEqual(stdev, "0.0")

        mock_calculate_stats.assert_called_once_with(data, self.mock_logger)

        mock_open.assert_called_once_with(
            os.path.join(self.output_dir, "results_1.csv"), "a", newline=""
        )
        mock_csv_writer.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "MLbackend.src.stats_analysis.calculate_stats", side_effect=mock_calculate_stats
    )
    def test_output_statistics_with_empty_data(self, mock_calculate_stats, mock_open):
        data = []
        metric = "test_metric"

        # Run the function
        metric, count, mean, stdev = output_statistics(
            2, data, metric, self.output_dir, self.mock_logger
        )
        # Assertions for empty data case
        self.assertEqual(metric, "test_metric")
        self.assertEqual(count, 0)
        self.assertEqual(mean, 0)
        self.assertEqual(stdev, 0)

        # Check that calculate_stats was not called for empty data
        mock_calculate_stats.assert_not_called()

        # Verify that file operations did not occur
        mock_open.assert_not_called()

    def tearDown(self):
        # Clean up the output directory if needed
        if os.path.exists(self.output_dir):
            os.rmdir(self.output_dir)


if __name__ == "__main__":
    unittest.main()
