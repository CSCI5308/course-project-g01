from flask import Flask, request, jsonify, send_file, render_template
from pathlib import Path
import re
import validators
import io
from src.devNetwork import communitySmellsDetector
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__,template_folder="../frontend/templates/",static_folder="../frontend/static/")


class InvalidInputError(Exception):
    pass


def validate_repo_url(url: str) -> None:

    if not url or not validators.url(url):
        raise InvalidInputError("Invalid repository URL format.")


def validate_email(email: str) -> None:

    if not email or not validators.email(email):
        raise InvalidInputError("Invalid email format.")


def validate_pat(token: str) -> None:

    if not re.match(r"^[a-zA-Z0-9-_]+$", token):
        raise ValueError("Invalid PAT format.")


@app.route("/")
def home():
    return render_template("index.html")





@app.route("/api/v1/smells", methods=["POST"])
def detect_smells():
    repo_url = request.form["repo-url"]
    email = request.form["email"]
    pat = request.form["access-token"]

    # Validate inputs
    try:
        validate_repo_url(repo_url)
        validate_email(email)
        validate_pat(pat)

    except InvalidInputError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    senti_strength_path: Path = Path(".", "data")
    output_path: Path = Path(".", "src", "results")
    global df

    try:
        # Call the function and save the result
        result,df = communitySmellsDetector(
            pat,
            repo_url,
            senti_strength_path,
            output_path,
        )
        print("Results:", result)
        # Check if result contains valid information
        if not result:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "No data found, Please try again later",
                    }
                ),
                404,
            )

        # Return successful response
        return render_template('results.html', data=result)

        
    except Exception as e:
        # Handle unexpected errors
        return jsonify({
            "status": "error",
            "message": "Something went wrong. Please try again later"
        }), 500  # Internal Server Error
    


@app.route("/api/v1/pdf", methods=["GET"])
def generate_pdf():
    if df is None or df.empty:
        return "DataFrame is empty or not initialized.", 400

    pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    pdf.drawString(100, height - 50, "Community Smell Report")
    pdf.drawString(100, height - 70, "Metric                Value")

    y_position = height - 100
    for index, row in df.iterrows():
        pdf.drawString(100, y_position, f"{row['Metric']: <20} {row['Value']}")
        y_position -= 20
        
        
        if y_position < 40:  
            pdf.showPage()  
            pdf.drawString(100, height - 50, "Community Smell Report")
            pdf.drawString(100, height - 70, "Metric                Value")
            y_position = height - 100  

    pdf.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name="smell_report.pdf", mimetype='application/pdf')
    

    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3001, debug=True)
