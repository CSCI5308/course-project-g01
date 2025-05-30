import csv
import os
import warnings
from logging import Logger
from typing import List, Dict

from joblib import load

from MLbackend.src.configuration import Configuration
from MLbackend.src.utils.result import Result

warnings.filterwarnings("ignore")


def smell_detection(config: Configuration, batch_idx: int, logger: Logger, result: Result) -> Dict[str, float]:

    # prepare results holder for easy mapping
    results = {}

    # open finalized results for reading
    project_csv_path = os.path.join(config.results_path, f"results_{batch_idx}.csv")
    with open(project_csv_path, newline="") as csv_file:
        rows = csv.reader(csv_file, delimiter=",")

        # parse into a dictionary
        for row in rows:
            results[row[0]] = row[1]

    metrics = build_metrics_list(results, logger)

    # load all models
    smells = ["OSE", "BCE", "PDE", "SV", "OS", "SD", "RS", "TF", "UI", "TC"]
    all_models = {}

    for smell in smells:
        model_path = os.path.abspath("MLbackend/models/{}.joblib".format(smell))
        all_models[smell] = load(model_path)

    # detect smells

    raw_smells = {
        smell_name: smell_model.predict(metrics)
        for smell_name, smell_model in all_models.items()
    }
    detected_smells = [smell for smell in smells if raw_smells[smell][0] == 1]
    for smell in smells:
        if raw_smells[smell][0] == 1:
            result.add_smell(batch_idx=batch_idx, smell=smell)

        # Prepare additional values
    additional_metrics = {"commit_count": results.get("commit_count", 0), "days_active": results.get("days_active", 0),
                          "FirstCommitDate": results.get("FirstCommitDate", ""),
                          "LastCommitDate": results.get("LastCommitDate", ""),
                          "AuthorCount": results.get("AuthorCount", 0),
                          "SponsoredAuthorCount": results.get("SponsoredAuthorCount", 0),
                          "PercentagesSponsoredAuthors": results.get("PercentageSponsoredAuthors", 0),
                          "AuthorCommitCount_mean": results.get("AuthorCommitCount_mean", 0),
                          "AuthorCommitCount_stdev": results.get("AuthorCommitCount_stdev", 0),
                          "NumberPRs": results.get("NumberPRs", 0),
                          "PRDuration_mean": results.get("PRDuration_mean", 0),
                          "PRCommentsLength_mean": results.get("PRCommentsLength_mean", 0),
                          "NumberIssues": results.get("NumberIssues", 0),
                          "IssueCommentsLength_mean": results.get("IssueCommentsLength_mean", 0),
                          "IssueCommentSentiments_mean": results.get("IssueCommentSentiments_mean", 0),
                          "NumberReleases": results.get("NumberReleases", 0),
                          "ReleaseCommitCount_mean": results.get("ReleaseCommitCount_mean", 0),
                          "BusFactorNumber": results.get("BusFactorNumber", 0),
                          "ExperiencedTFC": results.get("commitCentrality_TFC", 0),
                          "detected_smells": detected_smells.copy()}

    # insert detected smells
    detected_smells.insert(0, results["LastCommitDate"])
    additional_metrics["smell_results"] = detected_smells
    result.set_smell_results(additional_metrics)

    return additional_metrics


def build_metrics_list(results: dict, logger: Logger) -> List[List[float]]:

    # declare names to extract from the results file in the right order
    names: List[str] = [
        "AuthorCount",
        "DaysActive",
        "CommitCount",
        "AuthorCommitCount_stdev",
        "commitCentrality_NumberHighCentralityAuthors",
        "commitCentrality_PercentageHighCentralityAuthors",
        "SponsoredAuthorCount",
        "PercentageSponsoredAuthors",
        "NumberPRs",
        "PRParticipantsCount_stdev",
        "PRParticipantsCount_mean",
        "NumberIssues",
        "IssueParticipantCount_stdev",
        "IssueCountPositiveComments_mean",
        "commitCentrality_Centrality_count",
        "commitCentrality_Centrality_stdev",
        "commitCentrality_Betweenness_count",
        "commitCentrality_Closeness_count",
        "commitCentrality_Density",
        "commitCentrality_CommunityAuthorCount_count",
        "commitCentrality_CommunityAuthorItemCount_mean",
        "commitCentrality_CommunityAuthorItemCount_stdev",
        "commitCentrality_CommunityAuthorCount_mean",
        "commitCentrality_CommunityAuthorCount_stdev",
        "TimezoneCount",
        "TimezoneCommitCount_mean",
        "TimezoneCommitCount_stdev",
        "TimezoneAuthorCount_mean",
        "TimezoneAuthorCount_stdev",
        "NumberReleases",
        "ReleaseCommitCount_mean",
        "ReleaseCommitCount_stdev",
        "FN",
        "PRDuration_mean",
        "IssueDuration_mean",
        "BusFactorNumber",
        "commitCentrality_TFN",
        "commitCentrality_TFC",
        "PRCommentsCount_mean",
        "PRCommitsCount_mean",
        "NumberIssueComments",
        "IssueCommentsCount_mean",
        "IssueCommentsCount_stdev",
        "PRCommentsToxicityPercentage",
        "IssueCommentsToxicityPercentage",
        "RPCPR",
        "RPCIssue",
        "IssueCountNegativeComments_mean",
        "PRCountNegativeComments_mean",
        "ACCL",
    ]

    # build key/value list
    metrics: List[float] = []
    for name in names:

        # default value if key isn't present or the value is blank
        result: float = results.get(name) or 0
        if result == 0:
            logger.warning(
                f"No value for '{name}' during smell detection, defaulting to 0"
            )

        metrics.append(float(result))

    # return as a 2D array
    return [metrics]
