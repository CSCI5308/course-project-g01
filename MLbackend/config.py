import logging
from datetime import datetime
from logging import Logger
from pathlib import Path

LOG_FOLDER_PATH: Path = Path(".", "logs")
LOG_FOLDER_PATH.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FOLDER_PATH / f"log_{datetime.now():%Y-%m-%d_%H-%M-%S}.log",
)

LOGGER: Logger = logging.getLogger(__name__)
