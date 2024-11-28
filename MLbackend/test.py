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
import MLbackend.src.centrality_analysis as centrality
from dateutil.relativedelta import relativedelta
from MLbackend.src.alias_worker import replace_aliases
from src.commit_analysis import commit_analysis
from src.configuration import Configuration, parseDevNetworkArgs
from src.dev_analysis import dev_analysis
from src.graphql_analysis.issue_analysis import issue_analysis
from src.graphql_analysis.pr_analysis import pr_analysis
from src.graphql_analysis.release_analysis import release_analysis
from src.politeness_analysis import politeness_analysis
from MLbackend.src.repo_loader import getRepo
from MLbackend.src.smell_detection import smellDetection
from src.tag_analysis import tag_analysis


def community_smells_detector(config) -> dict:  # Specify the return type

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
            os.path.join(config.senti_strength_path, "SentiStrength.jar")
        )
        senti.setSentiStrengthLanguageFolderPath(
            os.path.join(config.senti_strength_path, "SentiStrength_Data")
        )

        # Prepare batch delta
        delta = relativedelta(months=+config.batch_months)

        # Handle aliases
        commits = list(replace_aliases(repo.iter_commits(), config))

        # Run analysis
        batch_dates, author_info_dict, days_active = commit_analysis(
            senti, commits, delta, config
        )

        tag_analysis(repo, delta, batch_dates, days_active, config)

        core_devs: List[List[Any]] = centrality.centrality_analysis(
            commits, delta, batch_dates, config
        )

        release_analysis(commits, config, delta, batch_dates)

        prParticipantBatches, pr_comment_batches = pr_analysis(
            config,
            senti,
            delta,
            batch_dates,
        )

        issueParticipantBatches, issue_comment_batches = issue_analysis(
            config,
            senti,
            delta,
            batch_dates,
        )

        politeness_analysis(config, pr_comment_batches, issue_comment_batches)

        for batch_idx, batch_date in enumerate(batch_dates):
            # Get combined author lists
            combined_authors_in_batch = (
                prParticipantBatches[batch_idx] + issueParticipantBatches[batch_idx]
            )

            # Build combined network
            centrality.build_grapql_network(
                batch_idx,
                combined_authors_in_batch,
                "issuesAndPRsCentrality",
                config,
            )

            # Get combined unique authors for both PRs and issues
            unique_authors_in_pr_batch = set(
                author for pr in prParticipantBatches[batch_idx] for author in pr
            )

            unique_authors_in_issue_batch = set(
                author for pr in issueParticipantBatches[batch_idx] for author in pr
            )

            unique_authors_in_batch = unique_authors_in_pr_batch.union(
                unique_authors_in_issue_batch
            )

            # Get batch core team
            batch_core_devs = core_devs[batch_idx]

            # Run dev analysis
            dev_analysis(
                author_info_dict,
                batch_idx,
                unique_authors_in_batch,
                batch_core_devs,
                config,
            )

            df = pd.read_csv(
                os.path.join(config.resultsPath, f"results_{batch_idx}.csv")
            )
            df.columns = ["Metric", "Value"]

            # Run smell detection and collect results
            smell_results = smellDetection(config, batch_idx)
            results = {
                "batch_date": batch_date.strftime("%Y-%m-%d"),
                "smell_results": list(smell_results),
                "core_devs": list(batch_core_devs),
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


def commit_date(tag):
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
    community_smells_detector(config)

