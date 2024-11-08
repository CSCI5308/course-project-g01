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
from MLbackend.src.politenessAnalysis import politenessAnalysis
from MLbackend.src.repoLoader import getRepo
from MLbackend.src.smellDetection import smellDetection
from MLbackend.src.tagAnalysis import tagAnalysis

smells = {
    "OSE": "Organizational Silo Effect: Isolated subgroups lead to poor communication, wasted resources, and duplicated code.",
    "BCE": "Black-cloud Effect: Information overload due to limited collaboration and a lack of experts, causing knowledge gaps.",
    "PDE": "Prima-donnas Effect: Resistance to external input due to ineffective collaboration, hindering team synergy.",
    "SV": "Sharing Villainy: Poor-quality information exchange results in outdated or incorrect knowledge being shared.",
    "OS": "Organizational Skirmish: Misaligned expertise and communication affect productivity, timelines, and costs.",
    "SD": "Solution Defiance: Conflicting technical opinions within subgroups cause delays and uncooperative behavior.",
    "RS": "Radio Silence: Formal, rigid procedures delay decision-making and waste time, leading to project delays.",
    "TFS": "Truck Factor Smell: Concentration of knowledge in few individuals leads to risks if they leave the project.",
    "UI": "Unhealthy Interaction: Weak, slow communication among developers, with low participation and long response times.",
    "TC": "Toxic Communication: Negative, hostile interactions among developers, resulting in frustration, stress, and potential project abandonment.",
}


def create_community_smell_report(
    pdf_file, metrics_results, meta_results, smell_abbreviations
):
    document = SimpleDocTemplate(pdf_file, pagesize=letter)
    content = []

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title = Paragraph("Community Smell Definitions and Metric Analysis", title_style)
    content.append(title)
    content.append(
        Paragraph("<br/><b>Community Smell Definitions:</b>", styles["Heading2"])
    )

    for smell_name in smell_abbreviations:
        smell_definition = smells.get(smell_name)
        if smell_definition:
            definition = f"{smell_name}: {smell_definition}"
            paragraph = Paragraph(definition, styles["Normal"])
            content.append(paragraph)

    commit_analysis_title = Paragraph("Commit Analysis:", styles["Heading2"])
    content.append(commit_analysis_title)

    commit_analysis_table = Table(meta_results)
    commit_analysis_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    content.append(commit_analysis_table)

    metrics_title = Paragraph(
        "<br/><b>Commit and PR Analysis Metrics:</b>", styles["Heading2"]
    )
    content.append(metrics_title)

    metrics_table = Table(metrics_results)
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    content.append(metrics_table)

    document.build(content)


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
            commitAnalysis(senti, commits, delta, config, logger)
        )

        tagres = tagAnalysis(repo, delta, batchDates, daysActive, config, logger)

        coreDevs: List[List[Any]] = centrality.centralityAnalysis(
            commits, delta, batchDates, config, logger
        )

        releaseres = releaseAnalysis(commits, config, delta, batchDates, logger)

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

        politeness = politenessAnalysis(
            config, prCommentBatches, issueCommentBatches, logger
        )

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
                "meta": results_meta,
                "metrics": results_metrics,
            }

            df = pd.read_csv(
                os.path.join(config.resultsPath, f"results_{batchIdx}.csv")
            )
            df.columns = ["Metric", "Value"]
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
