import argparse
import os
import shutil
import stat
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
import sentistrength
import src.centralityAnalysis as centrality
from dateutil.relativedelta import relativedelta
from src.aliasWorker import replaceAliases
from src.commitAnalysis import commitAnalysis
from src.configuration import Configuration, parseDevNetworkArgs
from src.devAnalysis import devAnalysis
from src.graphqlAnalysis.issueAnalysis import issueAnalysis
from src.graphqlAnalysis.prAnalysis import prAnalysis
from src.graphqlAnalysis.release_analysis import release_analysis
from src.politeness_analysis import politeness_analysis
from src.repoLoader import getRepo
from src.smellDetection import smellDetection
from src.tag_analysis import tag_analysis


def communitySmellsDetector(config) -> dict:  # Specify the return type

    results = {}  # Initialize a results dictionary
    df = None

    try:
        # Prepare folders
        if os.path.exists(config.resultsPath):
            remove_tree(config.resultsPath)

        os.makedirs(config.metricsPath)

        # Get repository reference
        repo = getRepo(config)

        # Setup sentiment analysis
        senti = sentistrength.PySentiStr()
        senti.setSentiStrengthPath(
            os.path.join(config.sentiStrengthPath, "SentiStrength.jar")
        )
        senti.setSentiStrengthLanguageFolderPath(
            os.path.join(config.sentiStrengthPath, "SentiStrength_Data")
        )

        # Prepare batch delta
        delta = relativedelta(months=+config.batchMonths)

        # Handle aliases
        commits = list(replaceAliases(repo.iter_commits(), config))

        # Run analysis
        batch_dates, authorInfoDict, days_active = commitAnalysis(
            senti, commits, delta, config
        )

        tag_analysis(repo, delta, batch_dates, days_active, config)

        coreDevs: List[List[Any]] = centrality.centralityAnalysis(
            commits, delta, batch_dates, config
        )

        release_analysis(commits, config, delta, batch_dates)

        prParticipantBatches, pr_comment_batches = prAnalysis(
            config,
            senti,
            delta,
            batch_dates,
        )

        issueParticipantBatches, issue_comment_batches = issueAnalysis(
            config,
            senti,
            delta,
            batch_dates,
        )

        politeness_analysis(config, pr_comment_batches, issue_comment_batches)

        for batch_idx, batchDate in enumerate(batch_dates):
            # Get combined author lists
            combinedAuthorsInBatch = (
                prParticipantBatches[batch_idx] + issueParticipantBatches[batch_idx]
            )

            # Build combined network
            centrality.buildGraphQlNetwork(
                batch_idx,
                combinedAuthorsInBatch,
                "issuesAndPRsCentrality",
                config,
            )

            # Get combined unique authors for both PRs and issues
            uniqueAuthorsInPrBatch = set(
                author for pr in prParticipantBatches[batch_idx] for author in pr
            )

            uniqueAuthorsInIssueBatch = set(
                author for pr in issueParticipantBatches[batch_idx] for author in pr
            )

            uniqueAuthorsInBatch = uniqueAuthorsInPrBatch.union(
                uniqueAuthorsInIssueBatch
            )

            # Get batch core team
            batchCoreDevs = coreDevs[batch_idx]

            # Run dev analysis
            devAnalysis(
                authorInfoDict,
                batch_idx,
                uniqueAuthorsInBatch,
                batchCoreDevs,
                config,
            )

            df = pd.read_csv(
                os.path.join(config.resultsPath, f"results_{batch_idx}.csv")
            )
            df.columns = ["Metric", "Value"]

            # Run smell detection and collect results
            smell_results = smellDetection(config, batch_idx)
            results = {
                "batch_date": batchDate.strftime("%Y-%m-%d"),
                "smell_results": list(smell_results),
                "core_devs": list(batchCoreDevs),
            }

            # Add more relevant results as needed

    except Exception as e:
        # Capture detailed error information
        error_message = str(e)
        error_traceback = traceback.format_exc()  # Get the full traceback

        # Return the detailed error
        results = {
            "status": "error",
            "message": error_message,
            "traceback": error_traceback,  # Include stack trace for debugging
        }
    finally:
        # Close repo to avoid resource leaks
        if "repo" in locals():
            del repo

    return results, df  # Return the collected results


def commitDate(tag):
    return tag.commit.committed_date


def remove_readonly(fn, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    remove_tree(path)


def remove_tree(path):
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=remove_readonly)
    else:
        os.remove(path)


if __name__ == "__main__":
    config = parseDevNetworkArgs(sys.argv[1:])
    communitySmellsDetector(config)
