import csv
import os
from logging import Logger
from statistics import StatisticsError, mean, stdev

from MLbackend.src.utils.result import Result


def output_statistics(
    idx: int,
    data: list,
    metric: str,
    output_dir: str,
    logger: Logger,
    result: Result = None,
):

    # validate
    if len(data) < 1:
        return metric, 0, 0, 0

    # calculate and output
    stats = calculate_stats(data, logger)

    # output
    with open(os.path.join(output_dir, f"results_{idx}.csv"), "a", newline="") as f:
        w = csv.writer(f, delimiter=",")

        for key in stats:
            output_value(w, metric, key, stats)

    if result:
        result.addMetricData(
            batch_idx=idx,
            metric=metric,
            count=stats["count"],
            mean=float(stats["mean"]),
            std_dev=stats["stdev"],
        )
    return (
        metric,
        stats["count"],
        f"{stats['mean']:.4f}",
        f"{stats['stdev']:.4f}" if stats["stdev"] else "0.0",
    )


def calculate_stats(data, logger: Logger):

    try:
        stats = dict(
            count=len(data),
            mean=mean(data) if len(data) > 0 else 0.0,
            stdev=stdev(data) if len(data) > 1 else None,
        )
    except StatisticsError:
        logger.error(f"There was a statistical error. The data was {data}")
        stats = dict()

    return stats


def output_value(w, metric: str, name: str, dict: dict):
    value = dict[name]
    name = "{0}_{1}".format(metric, name)
    w.writerow([name, value])
