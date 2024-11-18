
import os
import traceback
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from MLbackend.community_smells import detect_community_smells
from MLbackend.email_utils import configure_app
from MLbackend.validations import validate_input
from flask_mail import Message

app = Flask(
    __name__,
    template_folder="../frontend/templates/",
    static_folder="../frontend/static/",
)

configure_app(app)


@app.route("/")
def home():
    return render_template("index.html")




@app.route("/api/v1/smells", methods=["POST"])
def detect_smells():
    url = request.form["repo-url"]
    email = request.form["email"]
    pat = request.form["access-token"]

    try:
        validate_input(url, email, pat)
        result = detect_community_smells(url, pat)
        global pdf_path
        pdf_path = result.pdf_file_path

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

        send_email(email=email)
        return render_template("results.html", data=result.getWebResult())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




@app.route("/api/v1/pdf", methods=["GET"])
def generate_pdf():
    try:
        pdf_path1 = Path(pdf_path).resolve()
        return send_file(pdf_path1, as_attachment=True)
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Something went wrong. Please try again later",
                }
            ),
            500,
        )


def send_email(email):
    try:
        PDF_FILE_PATH = os.path.abspath(pdf_path)
        msg = Message(
            subject="Community Smells Detector",
            sender="g01communitysmellsdetector@gmail.com",
            recipients=[email],
        )
        msg.body = "Hey, PFA smells report"
        with app.open_resource(PDF_FILE_PATH) as fp:
            msg.attach("smell_report.pdf", "application/pdf", fp.read())

        app.mail.send(msg)
        return "Message sent!"
    except Exception as e:
        return str(e)
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
