import csv
import os
from logging import Logger

from src.configuration import Configuration


def devAnalysis(
    authorInfoDict: set,
    batchIdx: int,
    devs: set,
    coreDevs: set,
    config: Configuration,
    logger: Logger,
):

    # select experienced developers
    experiencedDevs = [
        login for login, author in authorInfoDict.items() if author["experienced"]
    ]

    # filter by developers present in list of aliased developers by commit
    numberActiveExperiencedDevs = len(devs.intersection(set(experiencedDevs)))

    # calculate bus factor
    try:
        busFactor = (len(devs) - len(coreDevs)) / len(devs)
    except ZeroDivisionError:
        logger.warning(
            f"There are no devs in this batch #{batchIdx}, so we are considering bus factor as 0"
        )
        busFactor = 0

    # calculate TFC
    commitCount = sum(
        [author["commitCount"] for login, author in authorInfoDict.items()]
    )
    sponsoredCommitCount = sum(
        [
            author["commitCount"]
            for login, author in authorInfoDict.items()
            if author["sponsored"]
        ]
    )
    experiencedCommitCount = sum(
        [
            author["commitCount"]
            for login, author in authorInfoDict.items()
            if author["experienced"]
        ]
    )

    sponsoredTFC = sponsoredCommitCount / commitCount * 100
    experiencedTFC = experiencedCommitCount / commitCount * 100

    logger.info("Writing developer analysis results")
    with open(
        os.path.join(config.resultsPath, f"results_{batchIdx}.csv"), "a", newline=""
    ) as f:
        w = csv.writer(f, delimiter=",")
        w.writerow(["NumberActiveExperiencedDevs", numberActiveExperiencedDevs])
        w.writerow(["BusFactorNumber", busFactor])
        w.writerow(["SponsoredTFC", sponsoredTFC])
        w.writerow(["ExperiencedTFC", experiencedTFC])
