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
        self.googleKey = google_key
        self.start_date = start_date

        # parse repo name into owner and project name
        split = self.repository_url.split("/")
        self.repository_owner = split[3]
        self.repository_name = split[4]

        # build repo path
        self.repository_path = os.path.join(self.output_path, split[3], split[4])

        # build results path
        self.results_path = os.path.join(self.repository_path, "results")

        # build metrics path
        self.metricsPath = os.path.join(self.results_path, "metrics")