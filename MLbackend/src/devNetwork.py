import os
import shutil
import stat
import traceback
from logging import Logger
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
import sentistrength
from dateutil.relativedelta import relativedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

import MLbackend.src.centralityAnalysis as centrality
from MLbackend.src.aliasWorker import replaceAliases
from MLbackend.src.commitAnalysis import commitAnalysis
from MLbackend.src.configuration import Configuration
from MLbackend.src.devAnalysis import devAnalysis
from MLbackend.src.graphqlAnalysis.issueAnalysis import issueAnalysis
from MLbackend.src.graphqlAnalysis.prAnalysis import prAnalysis
from MLbackend.src.graphqlAnalysis.releaseAnalysis import releaseAnalysis
from MLbackend.src.pdfGeneration import generate_pdf
from MLbackend.src.politenessAnalysis import politenessAnalysis
from MLbackend.src.repoLoader import getRepo
from MLbackend.src.smellDetection import smellDetection
from MLbackend.src.tagAnalysis import tagAnalysis
from MLbackend.src.utils.result import Result


def communitySmellsDetector(
    pat: str,
    repo_url: str,
    senti_strength_path: Path,
    output_path: Path,
    logger: Logger,
    result: Result,
    google_api_key: Optional[str] = None,
    batch_months: float = 9999,
    start_date: Optional[str] = None,
) -> None:  # Specify the return type
    

    pdf_results = {}
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
        batchDates, authorInfoDict, daysActive, results_meta, results_metrics = (
            commitAnalysis(senti, commits, delta, config, logger,result)
        )
        pdf_results["Commit Analysis"] = [results_meta,results_metrics]


        tagres = tagAnalysis(repo, delta, batchDates, daysActive, config, logger)


        coreDevs: List[List[Any]] = centrality.centralityAnalysis(
            commits, delta, batchDates, config, logger, result
        )

        releaseres = releaseAnalysis(commits, config, delta, batchDates, logger)

        prParticipantBatches, prCommentBatches, results_meta2, results_metrics2, results_meta3, results_metric3 = prAnalysis(
            config,
            senti,
            delta,
            batchDates,
            logger,
            None
        )
        pdf_results["PR Analysis"] = [results_meta2,results_metrics2]
        pdf_results["PR Comment Analysis"] = [results_meta3,results_metric3]

        issueParticipantBatches, issueCommentBatches, results_meta4, results_metrics4, results_meta5, results_metric5 = issueAnalysis(
            config,
            senti,
            delta,
            batchDates,
            logger,
            None
        )

        pdf_results["Issue Analysis"] = [results_meta4,results_metrics4]
        pdf_results["Issue Comment Analysis"] = [results_meta5,results_metric5]

        politeness = politenessAnalysis(
            config, prCommentBatches, issueCommentBatches, logger, result
        )
        pdf_results["Politeness Analysis"] = [politeness]

        dev_res = []
        meta_cent = []
        metrics_cent = []

        for batchIdx, batchDate in enumerate(batchDates):
            # Get combined author lists
            combinedAuthorsInBatch = (
                prParticipantBatches[batchIdx] + issueParticipantBatches[batchIdx]
            )

            # Build combined network
            authors, meta, metric = centrality.buildGraphQlNetwork(
                batchIdx,
                combinedAuthorsInBatch,
                "issuesAndPRsCentrality",
                config,
                logger,
                None,
            )
            meta_cent.append(meta)
            metrics_cent.append(metric)

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
            meta_res = devAnalysis(
                authorInfoDict,
                batchIdx,
                uniqueAuthorsInBatch,
                batchCoreDevs,
                config,
                logger,
            )
            dev_res.append(meta_res)

            smell_results = smellDetection(config, batchIdx, logger, result)
            pdf_results["IssuesAndPRsCentrality Analysis"] = [meta_cent[0],metrics_cent[0]]
            pdf_results["Dev Analysis"] =  dev_res
            result.setPDFFilePath(
                pdf_file_path=os.path.join(".", config.resultsPath, "smell_report.pdf")
            )
            generate_pdf(
                pdf_results=pdf_results,
                smells_det=smell_results["smell_results"][1:],
                pdf_file_path=result.pdf_file_path,
            )
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
