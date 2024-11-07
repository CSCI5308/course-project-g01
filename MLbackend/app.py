from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
from src.devNetwork import communitySmellsDetector
from reportlab.lib.pagesizes import letter
from flask_mail import Mail, Message
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
from config import LOGGER
from validations import validate_url, validate_email, validate_pat,InvalidInputError
import traceback


app = Flask(
    __name__,
    template_folder="../frontend/templates/",
    static_folder="../frontend/static/",
)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "g01communitysmellsdetector@gmail.com"
app.config["MAIL_PASSWORD"] = "gmki hznr hixx bihb"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
mail = Mail(app)

@app.route("/")
def home():
    return render_template("index.html")


def generate_pdf1(
    metrics_results, meta_results, smell_abbreviations, smells, PDF_FILE_PATH
):
    document = SimpleDocTemplate(PDF_FILE_PATH, pagesize=letter)
    content = []

    # Add title
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title = Paragraph("Community Smell Definitions and Metric Analysis", title_style)
    content.append(title)

    # Add community smell definitions
    for smell_name in smell_abbreviations:
        smell_definition = smells.get(smell_name)
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
    document.build(content)


output_path: Path = Path(".", "src", "results")


@app.route("/api/v1/smells", methods=["POST"])
def detect_smells():
    url = request.form["repo-url"]
    email = request.form["email"]
    pat = request.form["access-token"]

    senti_strength_path: Path = Path(".", "data")
    output_path: Path = Path(".", "src", "results")
    global result

    try:
        validate_url(url)
        validate_email(email)
        validate_pat(pat)
        result = communitySmellsDetector(
            pat, url, senti_strength_path, output_path, LOGGER
        )
        if not result:
            LOGGER.warning("No community smells detected.")
            return jsonify({"status": "error", "message": "No data found, Please try again later"}), 404
        
        send_email(email=email)
        return render_template("results.html", data=result)
    except InvalidInputError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        LOGGER.error(f"Unexpected error: {str(e)}")
        LOGGER.error(f"Stack trace:\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Something went wrong."}), 500

@app.route("/api/v1/pdf", methods=["GET"])
def generate_pdf():
    try:

        metrics_results = result["metrics"]
        meta_results = result["meta"]
        smell_abbreviations = result["smell_results"][1:]
        PDF_FILE_PATH = os.path.join(output_path, "smell_report.pdf")
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

        # Generate PDF
        generate_pdf1(
            metrics_results, meta_results, smell_abbreviations, smells, PDF_FILE_PATH
        )

        # Send the generated PDF to the frontend
        return send_file(PDF_FILE_PATH, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(email):
    PDF_FILE_PATH = os.path.join(output_path, "smell_report.pdf")
    metrics_results = result["metrics"]
    meta_results = result["meta"]
    smell_abbreviations = result["smell_results"][1:]
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
    generate_pdf1(
        metrics_results, meta_results, smell_abbreviations, smells, PDF_FILE_PATH
    )
    msg = Message(
        subject="Community Smells Detector",
        sender="g01communitysmellsdetector@gmail.com",
        recipients=[email],
    )
    msg.body = "Hey, PFA smells report"
    with app.open_resource(PDF_FILE_PATH) as fp:
        msg.attach("smell_report.pdf", "application/pdf", fp.read())
    mail.send(msg)


if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=3000)
    app.run(port=8000,debug=True)
