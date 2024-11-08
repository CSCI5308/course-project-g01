import os
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_mail import Mail, Message
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from MLbackend.config import LOGGER
from MLbackend.src.devNetwork import communitySmellsDetector
from MLbackend.validations import (InvalidInputError, validate_email,
                                   validate_pat, validate_url)

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

def build_pdf(pdf_results,smells,smells_det,pdf_file):
    document = SimpleDocTemplate(pdf_file, pagesize=letter)
    content = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']

    title = Paragraph("Community Smell Definitions and Metric Analysis", title_style)
    content.append(title)
    content.append(Paragraph("<br/><b>Detected Community Smell Definitions:</b>", styles['Heading2']))

    for smell_name, smell_definition in smells.items():
        if smell_name in smells_det:
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
        content.append(Paragraph(f"<br/><b>{i} :</b>", styles['Heading2']))

        if len(result) == 2:
            commit_data_1, commit_data_2 = result
            commit_table_data_1 = [[row[0], row[1]] for row in commit_data_1]
            commit_table_data_2 = commit_data_2
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




base_output_path: Path = Path(".", "MLbackend", "src", "results")

@app.route("/api/v1/smells", methods=["POST"])
def detect_smells():
    url = request.form["repo-url"]
    email = request.form["email"]
    pat = request.form["access-token"]
    global repo_output_path
    split = url.split("/")
    repository_path = Path(base_output_path, split[3], split[4])
    repo_output_path = Path(repository_path, "results")  # Unique output path for the repository
    senti_strength_path: Path = Path(".", "MLbackend", "data")
    output_path: Path = Path(".", "MLbackend", "src", "results")
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



def create_pdf():
    try:
        pdf_results = result["pdf_results"]
        smell_det = result["smell_results"][1:]
        PDF_FILE_PATH = os.path.abspath(os.path.join(repo_output_path, "community_smell_metrics.pdf"))
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
        res = build_pdf(pdf_results,smells,smell_det, PDF_FILE_PATH)
        return res
    except:
        return jsonify({
            "status": "error",
            "message": "Something went wrong. Please try again later"
        }), 500  # Internal Server Error

@app.route("/api/v1/pdf", methods=["GET"])
def generate_pdf():
    try:
        PDF_FILE_PATH = os.path.abspath(os.path.join(repo_output_path, "community_smell_metrics.pdf"))
        res = create_pdf()
        if not res:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "No data found, Please try again later",
                    }
                ),
                404,
            )

        return send_file(PDF_FILE_PATH, as_attachment=True)
    except Exception as e:
        LOGGER.error(f"Stack trace:\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": "Something went wrong. Please try again later"
        }), 500  # Internal Server Error

def send_email(email):
    PDF_FILE_PATH = os.path.abspath(os.path.join(repo_output_path, "community_smell_metrics.pdf"))

    res = create_pdf()
    msg = Message(
        subject='Community Smells Detector', 
        sender='g01communitysmellsdetector@gmail.com',  
        recipients=[email]  
    )
    msg.body = "Hey, PFA smells report"
    with app.open_resource(PDF_FILE_PATH) as fp:  
        msg.attach("smell_report.pdf", "application/pdf", fp.read()) 
    mail.send(msg)
    return "Message sent!"



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
