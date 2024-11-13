import logging
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Dict

LOG_FOLDER_PATH: Path = Path(".", "logs")
LOG_FOLDER_PATH.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FOLDER_PATH / f"log_{datetime.now():%Y-%m-%d_%H-%M-%S}.log",
)

LOGGER: Logger = logging.getLogger(__name__)

SMELLS_DEFINITION: Dict[str, str] = {
    "OSE": "Organizational Silo Effect: Isolated subgroups lead to poor communication, wasted resources, and duplicated code.",
    "BCE": "Black-cloud Effect: Information overload due to limited collaboration and a lack of experts, causing knowledge gaps.",
    "PDE": "Prima-donnas Effect: Resistance to external input due to ineffective collaboration, hindering team synergy.",
    "SV": "Sharing Villainy: Poor-quality information exchange results in outdated or incorrect knowledge being shared.",
    "OS": "Organizational Skirmish: Misaligned expertise and communication affect productivity, timelines, and costs.",
    "SD": "Solution Defiance: Conflicting technical opinions within subgroups cause delays and uncooperative behavior.",
    "RS": "Radio Silence: Formal, rigid procedures delay decision-making and waste time, leading to project delays.",
    "TFS": "Truck Factor Smell: Concentration of knowledge in few individuals leads to risks if they leave the project.",
    "UI": "Unhealthy Interaction: Weak, slow communication among developers, with low participation and long response times.",
    "TC": "Toxic Communication: Negative, hostile interactions among developers, resulting in frustration, stress, and potential project abandonment.",
}
