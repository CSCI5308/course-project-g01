from pathlib import Path
from MLbackend.src.dev_network import community_smells_detector
from MLbackend.config import LOGGER
from MLbackend.src.utils.result import Result


def detect_community_smells(url, pat):
    senti_strength_path = Path(".", "MLbackend", "data")
    output_path = Path(".", "MLbackend", "src", "results")
    result_ins: Result = Result(logger=LOGGER)

    community_smells_detector(
        pat=pat,
        repo_url=url,
        senti_strength_path=senti_strength_path,
        output_path=output_path,
        logger=LOGGER,
        result=result_ins,
    )
    if len(result_ins.smells) == 0:
        return None
    else:
        return result_ins
