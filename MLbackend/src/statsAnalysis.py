import csv
import os
from logging import Logger
from statistics import StatisticsError, mean, stdev


def outputStatistics(idx: int, data: list, metric: str, outputDir: str, logger: Logger):

    # validate
    if len(data) < 1:
        return

    # calculate and output
    stats = calculateStats(data, logger)

    # output
    with open(os.path.join(outputDir, f"results_{idx}.csv"), "a", newline="") as f:
        w = csv.writer(f, delimiter=",")

        for key in stats:
            outputValue(w, metric, key, stats)
    return (
        metric,
        stats["count"],
        f"{stats['mean']:.4f}",
        f"{stats['stdev']:.4f}" if stats["stdev"] else "N/A",
    )


def calculateStats(data, logger: Logger):

    try:
        stats = dict(
            count=len(data),
            mean=mean(data) if len(data) > 0 else 0,
            stdev=stdev(data) if len(data) > 1 else None,
        )
    except StatisticsError:
        logger.error(f"There was a statistical error. The data was {data}")

    return stats


def outputValue(w, metric: str, name: str, dict: dict):
    value = dict[name]
    name = "{0}_{1}".format(metric, name)
    w.writerow([name, value])
