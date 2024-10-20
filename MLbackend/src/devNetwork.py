import os
import shutil
import stat
import sentistrength
from pathlib import Path
from typing import Optional, List, Any
from logging import Logger

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
    logger: Logger,
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

        logger.info(f"Received a new request for {repo_url}.")

        logger.debug(f"Repository URL: {repo_url}")
        logger.debug(f"Batch Size: {batch_months} months")
        logger.debug(f"Output Path: {output_path}")
        logger.debug(f"SentiStrength Path: {senti_strength_path}")
        logger.debug(f"Max Distance: {0}")
        logger.debug(f"PAT: {pat}")
        logger.debug(f"Google Key: {google_api_key}")
        logger.debug(f"Start Date: {start_date}")

        # Prepare folders
        if os.path.exists(config.resultsPath):
            remove_tree(config.resultsPath)

        os.makedirs(config.metricsPath)

        # Get repository reference
        repo = getRepo(config, logger)

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
        commits = list(replaceAliases(repo.iter_commits(), config, logger))

        # Run analysis
        batchDates, authorInfoDict, daysActive = commitAnalysis(
            senti, commits, delta, config, logger
        )

        tagAnalysis(repo, delta, batchDates, daysActive, config, logger)

        coreDevs: List[List[Any]] = centrality.centralityAnalysis(
            commits, delta, batchDates, config, logger
        )

        releaseAnalysis(commits, config, delta, batchDates, logger)

        prParticipantBatches, prCommentBatches = prAnalysis(
            config,
            senti,
            delta,
            batchDates,
            logger,
        )

        issueParticipantBatches, issueCommentBatches = issueAnalysis(
            config,
            senti,
            delta,
            batchDates,
            logger,
        )

        politenessAnalysis(config, prCommentBatches, issueCommentBatches, logger)

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
                logger,
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
                logger,
            )

            # Run smell detection and collect results
            smell_results = smellDetection(config, batchIdx, logger)
            results = {
                "batch_date": batchDate.strftime("%Y-%m-%d"),
                "smell_results": list(smell_results),
                "core_devs": list(batchCoreDevs),
            }

            # Add more relevant results as needed

    except Exception as e:

        # Return the detailed error
        results = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
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
