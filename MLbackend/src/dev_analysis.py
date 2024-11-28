import csv
import os
from logging import Logger

from MLbackend.src.configuration import Configuration


def dev_analysis(
    author_info_dict: set,
    batch_idx: int,
    devs: set,
    core_devs: set,
    config: Configuration,
    logger: Logger,
):

    # select experienced developers
    experienced_devs = [
        login for login, author in author_info_dict.items() if author["experienced"]
    ]

    # filter by developers present in list of aliased developers by commit
    number_active_experienced_devs = len(devs.intersection(set(experienced_devs)))

    # calculate bus factor
    try:
        bus_factor = (len(devs) - len(core_devs)) / len(devs)
    except ZeroDivisionError:
        logger.warning(
            f"There are no devs in this batch #{batch_idx}, so we are considering bus factor as 0"
        )
        bus_factor = 0

    # calculate TFC
    commit_count = sum(
        [author["commit_count"] for login, author in author_info_dict.items()]
    )
    sponsored_commit_count = sum(
        [
            author["commit_count"]
            for login, author in author_info_dict.items()
            if author["sponsored"]
        ]
    )
    experienced_commit_count = sum(
        [
            author["commit_count"]
            for login, author in author_info_dict.items()
            if author["experienced"]
        ]
    )

    sponsored_tfc = sponsored_commit_count / commit_count * 100
    experienced_tfc = experienced_commit_count / commit_count * 100

    logger.info("Writing developer analysis results")
    with open(
        os.path.join(config.results_path, f"results_{batch_idx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["NumberActiveExperiencedDevs", number_active_experienced_devs])
        w.writerow(["BusFactorNumber", bus_factor])
        w.writerow(["SponsoredTFC", sponsored_tfc])
        w.writerow(["ExperiencedTFC", experienced_tfc])

    meta_res = [
        ["Metric", "Value"],
        ["NumberActiveExperiencedDevs", number_active_experienced_devs],
        ["BusFactorNumber", bus_factor],
        ["SponsoredTFC", sponsored_tfc],
        ["ExperiencedTFC", experienced_tfc],
    ]
    return meta_res
