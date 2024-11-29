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

import MLbackend.src.centrality_analysis as centrality
from MLbackend.src.alias_worker import replace_aliases
from MLbackend.src.commit_analysis import commit_analysis
from MLbackend.src.configuration import Configuration
from MLbackend.src.dev_analysis import dev_analysis
from MLbackend.src.graphql_analysis.issue_analysis import issue_analysis
from MLbackend.src.graphql_analysis.pr_analysis import pr_analysis
from MLbackend.src.graphql_analysis.release_analysis import release_analysis
from MLbackend.src.pdf_generation import generate_pdf
from MLbackend.src.politeness_analysis import politeness_analysis
from MLbackend.src.repo_loader import get_repo
from MLbackend.src.smell_detection import smell_detection
from MLbackend.src.tag_analysis import tag_analysis
from MLbackend.src.utils.result import Result


def community_smells_detector(
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
            repository_url=repo_url,
            batch_months=batch_months,
            output_path=output_path,
            senti_strength_path=senti_strength_path,
            max_distance=0,
            pat=pat,
            google_key=google_api_key,
            start_date=start_date,
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
        if os.path.exists(config.results_path):
            remove_tree(config.results_path)

        os.makedirs(config.metricsPath)

        # Get repository reference
        repo = get_repo(config, logger)

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
        commits = list(replace_aliases(repo.iter_commits(), config, logger))
        

        # Run analysis
        batch_dates, author_info_dict, days_active, results_meta, results_metrics = (
            commit_analysis(senti, commits, delta, config, logger,result)
        )
        pdf_results["Commit Analysis"] = [results_meta, results_metrics]


        tag_res = tag_analysis(repo, delta, batch_dates, days_active, config, logger)

        core_devs: List[List[Any]] = centrality.centrality_analysis(
            commits, delta, batch_dates, config, logger, result
        )

        release_res = release_analysis(commits, config, delta, batch_dates, logger)

        (
            pr_participant_batches,
            pr_comment_batches,
            results_meta2,
            results_metrics2,
            results_meta3,
            results_metric3,
        ) = pr_analysis(
            config,
            senti,
            delta,
            batch_dates,
            logger,
            None
        )
        pdf_results["PR Analysis"] = [results_meta2, results_metrics2]
        pdf_results["PR Comment Analysis"] = [results_meta3, results_metric3]

        (
            issue_participant_batches,
            issue_comment_batches,
            results_meta4,
            results_metrics4,
            results_meta5,
            results_metric5,
        ) = issue_analysis(
            config,
            senti,
            delta,
            batch_dates,
            logger,
            None
        )

        pdf_results["Issue Analysis"] = [results_meta4, results_metrics4]
        pdf_results["Issue Comment Analysis"] = [results_meta5, results_metric5]

        politeness = politeness_analysis(
            config, pr_comment_batches, issue_comment_batches, logger, result
        )
        pdf_results["Politeness Analysis"] = [politeness]

        dev_res = []
        meta_cent = []
        metrics_cent = []

        for batch_idx, batch_date in enumerate(batch_dates):
            # Get combined author lists
            combined_authors_in_batch = (
                pr_participant_batches[batch_idx] + issue_participant_batches[batch_idx]
            )

            # Build combined network
            authors, meta, metric = centrality.build_grapql_network(
                batch_idx,
                combined_authors_in_batch,
                "issuesAndPRsCentrality",
                config,
                logger,
                None,
            )
            meta_cent.append(meta)
            metrics_cent.append(metric)

            # Get combined unique authors for both PRs and issues
            unique_authors_in_pr_batch = set(
                author for pr in pr_participant_batches[batch_idx] for author in pr
            )

            unique_authors_in_issue_batch = set(
                author for pr in issue_participant_batches[batch_idx] for author in pr
            )

            unique_authors_in_batch = unique_authors_in_pr_batch.union(
                unique_authors_in_issue_batch
            )

            # Get batch core team
            batch_core_devs = core_devs[batch_idx]

            # Run dev analysis
            meta_res = dev_analysis(
                author_info_dict,
                batch_idx,
                unique_authors_in_batch,
                batch_core_devs,
                config,
                logger,
            )
            dev_res.append(meta_res)

            smell_results = smell_detection(config, batch_idx, logger, result)
            pdf_results["IssuesAndPRsCentrality Analysis"] = [meta_cent[0],metrics_cent[0]]
            pdf_results["Dev Analysis"] =  dev_res
            result.set_pdf_file_path(
                pdf_file_path=os.path.join(".", config.results_path, "smell_report.pdf")
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
