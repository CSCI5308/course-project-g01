from logging import Logger
from typing import Any, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from MLbackend.config import LOGGER, SMELLS_DEFINITION


def generate_pdf(
    metrics_results: (
        List[List[Tuple[str, int, float, float]]] | List[Tuple[str, int, float, float]]
    ),
    meta_results: List[List[List[Any]]] | List[List[Any]],
    smell_abbreviations: List[List[str]] | List[str],
    pdf_file_path: str,
    logger: Logger,
):
    document = SimpleDocTemplate(str(pdf_file_path), pagesize=letter)
    content = []

    # Add title
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title = Paragraph("Community Smell Definitions and Metric Analysis", title_style)
    content.append(title)

    # Add community smell definitions
    for smell_name in smell_abbreviations:
        smell_definition = SMELLS_DEFINITION.get(smell_name)
        if smell_definition:
            definition = f"{smell_name}: {smell_definition}"
            paragraph = Paragraph(definition, styles["Normal"])
            content.append(paragraph)
    # Add a page break after the definitions
    content.append(Paragraph("<br/>", styles["Normal"]))

    # Add Commit Analysis section
    commit_analysis_title = Paragraph("Commit Analysis:", styles["Heading2"])
    content.append(commit_analysis_title)

    # Commit Analysis Table
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

    # Add Metrics section
    metrics_title = Paragraph(
        "<br/><b>Commit and PR Analysis Metrics:</b>", styles["Heading2"]
    )
    content.append(metrics_title)

    # Metrics Table
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

    # Build the PDF
    try:
        document.build(content)
    except Exception as e:
        LOGGER.error(f"Failed to build PDF: {e}")
