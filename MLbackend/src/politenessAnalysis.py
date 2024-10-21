import os
import csv
import convokit

import src.statsAnalysis as stats
from src.configuration import Configuration


def politenessAnalysis(
    config: Configuration,
    prCommentBatches: list,
    issueCommentBatches: list,
) -> None:

    calculateACCL(config, prCommentBatches, issueCommentBatches)

    calculateRPC(config, "PR", prCommentBatches)
    calculateRPC(config, "Issue", prCommentBatches)


def calculateACCL(config, prCommentBatches, issueCommentBatches) -> None:
    for batchIdx, batch in enumerate(prCommentBatches):

        prCommentLengths = list([len(c) for c in batch])
        issueCommentBatch = list([len(c) for c in issueCommentBatches[batchIdx]])

        prCommentLengthsMean = stats.calculateStats(prCommentLengths)["mean"]
        issueCommentLengthsMean = stats.calculateStats(issueCommentBatch)["mean"]

        accl = prCommentLengthsMean + issueCommentLengthsMean / 2

        # output results
        with open(
            os.path.join(config.resultsPath, f"results_{batchIdx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["ACCL", accl])


def calculateRPC(config, outputPrefix, commentBatches) -> None:
    for batchIdx, batch in enumerate(commentBatches):

        # analyze batch
        positiveMarkerCount = getResults(batch) if len(batch) > 0 else 0.0

        # output results
        with open(
            os.path.join(config.resultsPath, f"results_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow([f"RPC{outputPrefix}", positiveMarkerCount])


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
    parser = convokit.TextParser(verbosity=1000)
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
