import os
import shutil
import stat
import sentistrength
from pathlib import Path
from typing import Optional, List, Any

import traceback  
from configuration import Configuration
from repoLoader import getRepo
from aliasWorker import replaceAliases
from commitAnalysis import commitAnalysis
import centralityAnalysis as centrality
from tagAnalysis import tagAnalysis
from devAnalysis import devAnalysis
from graphqlAnalysis.releaseAnalysis import releaseAnalysis
from graphqlAnalysis.prAnalysis import prAnalysis
from graphqlAnalysis.issueAnalysis import issueAnalysis
from smellDetection import smellDetection
from politenessAnalysis import politenessAnalysis
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

        print(
            "repositoryUrl: ", repo_url, "\n"
            "batchMonths: ", batch_months, "\n"
            "outputPath: ", output_path, "\n"
            "sentiStrengthPath: ", senti_strength_path, "\n"
            "maxDistance: ", 0, "\n"
            "pat: ", pat, "\n"
            "googleKey: ", google_api_key, "\n"
            "startDate: ", start_date
            )


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
            results[f'batch_{batchIdx}'] = {
                'batch_date': str(batchDate), 
                'smell_results': smell_results,
                'authors': ', '.join(uniqueAuthorsInBatch),
                'core_devs': batchCoreDevs,
                # Add more relevant results as needed
            }
    except Exception as e:
    # Capture detailed error information
        error_message = str(e)
        error_traceback = traceback.format_exc()  # Get the full traceback
        
        # Return the detailed error
        results = {
            "status": "error",
            "message": error_message,
            "traceback": error_traceback  # Include stack trace for debugging
        }
    finally:
        # Close repo to avoid resource leaks
        if "repo" in locals():
            del repo

    return results  # Return the collected results

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
