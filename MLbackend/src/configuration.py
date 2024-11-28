import argparse
import os
from typing import Sequence


class Configuration:
    def __init__(
        self,
        repository_url: str,
        batch_months: int,
        output_path: str,
        senti_strength_path: str,
        max_distance: int,
        pat: str,
        google_key: str,
        start_date: str,
    ):
        self.repository_url = repository_url
        self.batch_months = batch_months
        self.output_path = output_path
        self.senti_strength_path = senti_strength_path
        self.max_distance = max_distance
        self.pat = pat
        self.google_key = google_key
        self.start_date = start_date

        # parse repo name into owner and project name
        split = self.repository_url.split("/")
        self.repositoryOwner = split[3]
        self.repositoryName = split[4]

        # build repo path
        self.repositoryPath = os.path.join(self.output_path, split[3], split[4])

        # build results path
        self.resultsPath = os.path.join(self.repositoryPath, "results")

        # build metrics path
        self.metricsPath = os.path.join(self.resultsPath, "metrics")


def parseDevNetworkArgs(args: Sequence[str]):

    parser = argparse.ArgumentParser(
        description="Perform network and statistical analysis on GitHub repositories.",
        epilog="Check README file for more information on running this tool.",
    )

    parser.add_argument(
        "-p",
        "--pat",
        help="GitHub PAT (personal access token) used for querying the GitHub API",
        required=True,
    )

    parser.add_argument(
        "-g",
        "--google_key",
        help="Google Cloud API Key used for authentication with the Perspective API",
        required=False,
    )

    parser.add_argument(
        "-r",
        "--repository_url",
        help="GitHub repository URL that you want to analyse",
        required=True,
    )

    parser.add_argument(
        "-m",
        "--batch_months",
        help="Number of months to analyze per batch. Default=9999",
        type=float,
        default=9999,
    )

    parser.add_argument(
        "-s",
        "--senti_strength_path",
        help="local directory path to the SentiStregth tool",
        required=True,
    )

    parser.add_argument(
        "-o",
        "--output_path",
        help="Local directory path for analysis output",
        required=True,
    )

    parser.add_argument(
        "-sd",
        "--start_date",
        help="Start date of project life",
        required=False,
    )

    args = parser.parse_args()
    config = Configuration(
        args.repositoryUrl,
        args.batchMonths,
        args.outputPath,
        args.sentiStrengthPath,
        0,
        args.pat,
        args.googleKey,
        args.start_date,
    )

    return config
