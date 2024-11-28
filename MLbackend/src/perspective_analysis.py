import json
import math
import time
from datetime import datetime, timezone
from logging import Logger
from typing import List

import requests

from MLbackend.src.configuration import Configuration
from requests import RequestException


class ToxicityAnalysisError(Exception):
    """Custom exception for errors occurring during toxicity analysis."""
    pass

def get_toxicity_percentage(config: Configuration, comments: List[str], logger: Logger) -> float:

    if config.google_key is None:
        return 0
    # comment out to pause toxicity analysis
    # return 0

    # estimate completion
    qps_limit = 1
    buffer = 5
    query_limit = (qps_limit * 60) - buffer

    toxicity_minutes = math.ceil(len(comments) / query_limit)
    logger.info(
        f"Toxicity per comment, expecting around {toxicity_minutes} minute(s) completion time"
    )

    # declare toxicity results store
    toxic_results = 0

    # wait until the next minute
    sleep_until_next_minute()

    # run analysis
    for idx, comment in enumerate(comments):

        # build request
        url = (
            "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
            + "?key="
            + config.google_key
        )
        data_dict = {
            "comment": {"text": comment},
            "languages": ["en"],
            "requestedAttributes": {"TOXICITY": {}},
        }

        try:
            # send request
            response = requests.post(url=url, data=json.dumps(data_dict))
            response.raise_for_status()  # Raise an HTTPError if the response was unsuccessful
            parsed_response = response.json()

            toxicity = float(
                parsed_response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
            )

            # add to results store if toxic
            if toxicity >= 0.5:
                toxic_results += 1

        except RequestException as req_err:
            logger.error(f"Request error: {req_err}")
            raise ToxicityAnalysisError(f"Request error: {req_err}") from req_err

        except KeyError as key_err:
            logger.error("Response parsing error: Missing expected keys.")
            raise ToxicityAnalysisError("Response parsing error: Missing expected keys.") from key_err

        except ValueError as val_err:
            logger.error("Invalid toxicity value in response.")
            raise ToxicityAnalysisError("Invalid toxicity value in response.") from val_err

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ToxicityAnalysisError(f"Unexpected error: {e}") from e

        # we are only allowed 1 QPS, wait for a minute
        if (idx + 1) % query_limit == 0:
            logger.info("QPS limit reached, napping")
            sleep_until_next_minute()
            logger.info("processing")

    # calculate percentage of toxic comments
    percentage = 0 if len(comments) == 0 else toxic_results / len(comments)

    return percentage


def sleep_until_next_minute():
    t = datetime.now(timezone.utc)
    sleep_time = 60 - (t.second + t.microsecond / 1000000.0)
    time.sleep(sleep_time)
