import os
import csv
import convokit

from logging import Logger
import src.statsAnalysis as stats
from src.configuration import Configuration


def politenessAnalysis(
    config: Configuration,
    prCommentBatches: list,
    issueCommentBatches: list,
    logger: Logger,
) -> None:

    accl = calculateACCL(config, prCommentBatches, issueCommentBatches, logger)

    rpc_pr = calculateRPC(config, "PR", prCommentBatches, logger)
    rpc_issues = calculateRPC(config, "Issue", prCommentBatches, logger)
    return (accl, rpc_pr, rpc_issues)


def calculateACCL(config, prCommentBatches, issueCommentBatches, logger) -> None:
    logger.info(
        "Calculating Average Comment Character Length based on comments in PRs and Issues batches."
    )

    accls = []
    for batchIdx, batch in enumerate(prCommentBatches):

        prCommentLengths = list([len(c) for c in batch])
        issueCommentBatch = list([len(c) for c in issueCommentBatches[batchIdx]])

        prCommentLengthsMean = stats.calculateStats(prCommentLengths, logger)["mean"]
        issueCommentLengthsMean = stats.calculateStats(issueCommentBatch, logger)[
            "mean"
        ]

        accl = prCommentLengthsMean + issueCommentLengthsMean / 2
        accls.append(accl)

        # output results
        with open(
            os.path.join(config.resultsPath, f"results_{batchIdx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["ACCL", accl])
    return accls


def calculateRPC(config, outputPrefix, commentBatches, logger: Logger) -> None:
    logger.info(f"Calculating Relative positive count for {outputPrefix}s.")
    rpcs = []
    for batchIdx, batch in enumerate(commentBatches):

        # analyze batch
        positiveMarkerCount = getResults(batch) if len(batch) > 0 else 0.0
        rpcs.append((outputPrefix, positiveMarkerCount))

        # output results
        with open(
            os.path.join(config.resultsPath, f"results_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow([f"RPC{outputPrefix}", positiveMarkerCount])
    return rpcs


def getResults(comments: list) -> float:

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
    positiveMarkerCount = sum(
        [
            feature["feature_politeness_==HASPOSITIVE=="]
            for feature in features["meta.politeness_strategies"]
        ]
    )

    return positiveMarkerCount
