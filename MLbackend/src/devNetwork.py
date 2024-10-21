import os
import shutil
import stat
import sentistrength
from pathlib import Path
from typing import Optional, List, Any
from datetime import datetime
import pandas as pd

import traceback
from src.configuration import Configuration
from src.repoLoader import getRepo
from src.aliasWorker import replaceAliases
from src.commitAnalysis import commitAnalysis
import src.centralityAnalysis as centrality
from src.tagAnalysis import tagAnalysis
from src.devAnalysis import devAnalysis
from src.graphqlAnalysis.releaseAnalysis import releaseAnalysis
from src.graphqlAnalysis.prAnalysis import prAnalysis
from src.graphqlAnalysis.issueAnalysis import issueAnalysis
from src.smellDetection import smellDetection
from src.politenessAnalysis import politenessAnalysis
from dateutil.relativedelta import relativedelta

def communitySmellsDetector(
    pat: str,
    repo_url: str,
    senti_strength_path: Path,
    output_path: Path,
    google_api_key: Optional[str] = None,
    batch_months: float = 9999,
    start_date: Optional[str] = None,
) -> dict:  # Specify the return type

    results = {}  # Initialize a results dictionary
    df = None

    try:
        # Parse args
        config: Configuration = Configuration(
            repositoryUrl=repo_url,
            batchMonths=batch_months,
            outputPath=output_path,
            sentiStrengthPath=senti_strength_path,
            maxDistance=0,
            pat=pat,
            googleKey=google_api_key,
            startDate=start_date,
        )

        print(f"-- Repository URL: {repo_url}")
        print(f"-- Batch Size: {batch_months} months")
        print(f"-- Output Path: {output_path}")
        print(f"-- SentiStrength Path: {senti_strength_path}")
        print(f"-- Max Distance: {0}")
        print(f"-- PAT: {pat}")
        print(f"-- Google Key: {google_api_key}")
        print(f"-- Start Date: {start_date}")

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
        batchDates, authorInfoDict, daysActive = commitAnalysis(
            senti, commits, delta, config
        )

        tagAnalysis(repo, delta, batchDates, daysActive, config)

        coreDevs: List[List[Any]] = centrality.centralityAnalysis(
            commits, delta, batchDates, config
        )

        releaseAnalysis(commits, config, delta, batchDates)

        prParticipantBatches, prCommentBatches = prAnalysis(
            config,
            senti,
            delta,
            batchDates,
        )

        issueParticipantBatches, issueCommentBatches = issueAnalysis(
            config,
            senti,
            delta,
            batchDates,
        )

        politenessAnalysis(config, prCommentBatches, issueCommentBatches)

        for batchIdx, batchDate in enumerate(batchDates):
            # Get combined author lists
            combinedAuthorsInBatch = (
                prParticipantBatches[batchIdx] + issueParticipantBatches[batchIdx]
            )

            # Build combined network
            centrality.buildGraphQlNetwork(
                batchIdx,
                combinedAuthorsInBatch,
                "issuesAndPRsCentrality",
                config,
            )

            # Get combined unique authors for both PRs and issues
            uniqueAuthorsInPrBatch = set(
                author for pr in prParticipantBatches[batchIdx] for author in pr
            )

            uniqueAuthorsInIssueBatch = set(
                author for pr in issueParticipantBatches[batchIdx] for author in pr
            )

            uniqueAuthorsInBatch = uniqueAuthorsInPrBatch.union(
                uniqueAuthorsInIssueBatch
            )

            # Get batch core team
            batchCoreDevs = coreDevs[batchIdx]

            # Run dev analysis
            devAnalysis(
                authorInfoDict,
                batchIdx,
                uniqueAuthorsInBatch,
                batchCoreDevs,
                config,
            )

            # Run smell detection and collect results
            smell_results = smellDetection(config, batchIdx)
            results = {
                        "batch_date": batchDate.strftime("%Y-%m-%d"),
                        "smell_results": list(smell_results),
                        "core_devs": list(batchCoreDevs),
                    }

                # Add more relevant results as needed
            df = pd.read_csv(os.path.join(config.resultsPath, f"results_{batchIdx}.csv"))
            df.columns=["Metric", "Value"]
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
            

    return results,df  # Return the collected results


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

