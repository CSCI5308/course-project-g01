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
    "TC": "Toxic Communication: Negative, hostile interactions among developers, resulting in frustration, stress, and potential project abandonment."
}



def create_community_smell_report(pdf_results):
    pdf_file = "smell_report.pdf"
    document = SimpleDocTemplate(pdf_file, pagesize=letter)
    content = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']

    title = Paragraph("Community Smell Definitions and Metric Analysis", title_style)
    content.append(title)
    content.append(Paragraph("<br/><b>Detected Community Smell Definitions:</b>", styles['Heading2']))

    for smell_name, smell_definition in smells.items():
        paragraph = Paragraph(f"<b>{smell_name}:</b> {smell_definition}", normal_style)
        content.append(paragraph)

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    for i, result in pdf_results.items():
        content.append(Paragraph(f"<br/><b>{i} Analysis:</b>", styles['Heading2']))

        if len(result) == 2:
            commit_data_1, commit_data_2 = result
            commit_table_data_1 = [[row[0], row[1]] for row in commit_data_1]
            commit_table_data_2 = [[row[0], row[1], row[2], row[3]] for row in commit_data_2]
            commit_table_1 = Table(commit_table_data_1)
            commit_table_1.setStyle(table_style)
            commit_table_2 = Table(commit_table_data_2)
            commit_table_2.setStyle(table_style)
            content.append(commit_table_1)
            content.append(Paragraph("<br/>", styles['Heading2']))
            content.append(Paragraph("<br/>", styles['Heading2']))
            content.append(commit_table_2)
        else:
            commit_data = result[0]
            commit_table_data = [[row[0],row[1]] for row in commit_data]
            commit_table = Table(commit_table_data)
            commit_table.setStyle(table_style)
            content.append(commit_table)
    document.build(content)
    return pdf_file






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
            commitAnalysis(senti, commits, delta, config, logger)
        )
        pdf_results["Commit Analysis"] = [results_meta,results_metrics]

        tagres = tagAnalysis(repo, delta, batchDates, daysActive, config, logger)


        coreDevs: List[List[Any]] = centrality.centralityAnalysis(
            commits, delta, batchDates, config, logger
        )

        releaseres = releaseAnalysis(commits, config, delta, batchDates, logger)

        prParticipantBatches, prCommentBatches, results_meta2, results_metrics2, results_meta3, results_metric3 = prAnalysis(
            config,
            senti,
            delta,
            batchDates,
            logger,
        )
        pdf_results["PR Analysis"] = [results_meta2,results_metrics2]
        pdf_results["PR Comment Analysis"] = [results_meta3,results_metric3]

        issueParticipantBatches, issueCommentBatches, results_meta4, results_metrics4, results_meta5, results_metric5 = issueAnalysis(
            config,
            senti,
            delta,
            batchDates,
            logger,
        )

        pdf_results["Issue Analysis"] = [results_meta4,results_metrics4]
        pdf_results["Issue Comment Analysis"] = [results_meta5,results_metric5]

        politeness = politenessAnalysis(
            config, prCommentBatches, issueCommentBatches, logger
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


            # Run smell detection and collect results
            smell_results = smellDetection(config, batchIdx, logger)
            pdf_results["IssuesAndPRsCentrality Analysis"] = [meta_cent[0],metrics_cent[0]]
            pdf_results["Dev Analysis"] =  dev_res
            results = {
                "batch_date": batchDate.strftime("%Y-%m-%d"),
                **smell_results,
                "core_devs": list(batchCoreDevs),
                "pdf_results":pdf_results,
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

    return results


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