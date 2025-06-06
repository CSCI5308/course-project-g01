
import os
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_mail import Message

from MLbackend.community_smells import detect_community_smells
from MLbackend.email_utils import configure_app
from MLbackend.validations import validate_email,validate_pat,validate_url,InvalidInputError
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
        validate_url(url)
        validate_email(email)
        validate_pat(pat)
        result = detect_community_smells(url, pat)
        global pdf_path
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
        pdf_path = result.pdf_file_path
        send_email(email=email)
        return render_template("results.html", data=result.get_web_result())
    except InvalidInputError as input_error:
        return jsonify({"status": "error", "message": str(input_error)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/v1/pdf", methods=["GET"])
def generate_pdf():
    try:
        pdf_path1 = Path(pdf_path).resolve()
        return send_file(pdf_path1, as_attachment=True)
    except Exception as _:
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
