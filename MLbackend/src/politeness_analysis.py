import csv
import os
from logging import Logger
from typing import Any, List, Tuple

import convokit

import MLbackend.src.stats_analysis as stats
from MLbackend.src.configuration import Configuration
from MLbackend.src.utils.result import Result


def politeness_analysis(
    config: Configuration,
    pr_comment_batches: list,
    issue_comment_batches: list,
    logger: Logger,
    result: Result,
) -> List[List[Any]]:

    accl = calculate_accl(config, pr_comment_batches, issue_comment_batches, logger)
    rpc_pr = calculate_rpc(config, "PR", pr_comment_batches, logger)
    rpc_issues = calculate_rpc(config, "Issue", pr_comment_batches, logger)
    results = [
        ["Metrics", "Value"],
        ["ACCL", accl],
        ["RPCPR", rpc_pr[1]],
        ["RPCIssue", rpc_issues[1]],
    ]
    return results


def calculate_accl(
    config, pr_comment_batches, issue_comment_batches, logger
) -> Tuple[str, float]:
    logger.info(
        "Calculating Average Comment Character Length based on comments in PRs and Issues batches."
    )

    accls = []
    for batch_idx, batch in enumerate(pr_comment_batches):

        pr_comment_lengths = list([len(c) for c in batch])
        issue_comment_batch = list([len(c) for c in issue_comment_batches[batch_idx]])

        pr_comment_lengths_mean = stats.calculate_stats(pr_comment_lengths, logger)["mean"]
        issue_comment_lengths_mean = stats.calculate_stats(issue_comment_batch, logger)[
            "mean"
        ]

        accl = pr_comment_lengths_mean + issue_comment_lengths_mean / 2
        accls.append(accl)

        # output results
        with open(
            os.path.join(config.results_path, f"results_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["ACCL", accl])
    return accls[0]


def calculate_rpc(
    config, output_prefix, comment_batches, logger: Logger
) -> Tuple[str, float]:
    logger.info(f"Calculating Relative positive count for {output_prefix}s.")
    rpcs = []
    for batch_idx, batch in enumerate(comment_batches):

        # analyze batch
        positive_marker_count = get_results(batch) if len(batch) > 0 else 0.0
        rpcs.append((output_prefix, positive_marker_count))

        # output results
        with open(
            os.path.join(config.results_path, f"results_{batch_idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow([f"RPC{output_prefix}", positive_marker_count])
    return rpcs[0]


def get_results(comments: list) -> float:

    # define default speaker
    speaker = convokit.Speaker(id="default")

    # build utterance list
    utterances = list(
        [
            convokit.Utterance(id=str(idx), speaker=speaker, text=comment)
            for idx, comment in enumerate(comments)
        ]
    )

    # build corpus
    corpus = convokit.Corpus(utterances=utterances)

    # parse
    parser = convokit.TextParser(verbosity=0)
    corpus = parser.transform(corpus)

    # extract politeness features
    politeness = convokit.PolitenessStrategies()
    corpus = politeness.transform(corpus, markers=True)
    features = corpus.get_utterances_dataframe()

    # get positive politeness marker count
    positive_marker_count = sum(
        [
            feature["feature_politeness_==HASPOSITIVE=="]
            for feature in features["meta.politeness_strategies"]
        ]
    )

    return positive_marker_count
