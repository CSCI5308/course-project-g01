from logging import Logger
from typing import Any, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from MLbackend.config import LOGGER

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


def generate_pdf(pdf_results, smells_det, pdf_file_path):
    document = SimpleDocTemplate(str(pdf_file_path), pagesize=letter)

    content = []

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal_style = styles["Normal"]

    title = Paragraph("Community Smell Definitions and Metric Analysis", title_style)
    content.append(title)
    content.append(
        Paragraph(
            "<br/><b>Detected Community Smell Definitions:</b>", styles["Heading2"]
        )
    )

    for smell_name, smell_definition in smells.items():
        if smell_name in smells_det:
            paragraph = Paragraph(
                f"<b>{smell_name}:</b> {smell_definition}", normal_style
            )
            content.append(paragraph)

    table_style = TableStyle(
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

    for i, result in pdf_results.items():
        content.append(Paragraph(f"<br/><b>{i} :</b>", styles["Heading2"]))

        if len(result) == 2:
            commit_data_1, commit_data_2 = result
            commit_table_data_1 = [[row[0], row[1]] for row in commit_data_1]
            commit_table_data_2 = commit_data_2
            commit_table_1 = Table(commit_table_data_1)
            commit_table_1.setStyle(table_style)
            commit_table_2 = Table(commit_table_data_2)
            commit_table_2.setStyle(table_style)
            content.append(commit_table_1)
            content.append(Paragraph("<br/>", styles["Heading2"]))
            content.append(Paragraph("<br/>", styles["Heading2"]))
            content.append(commit_table_2)
        else:
            commit_data = result[0]
            commit_table_data = [[row[0], row[1]] for row in commit_data]
            commit_table = Table(commit_table_data)
            commit_table.setStyle(table_style)
            content.append(commit_table)
    try:
        document.build(content)
    except Exception as e:
        LOGGER.error(f"Failed to build PDF: {e}")
