import os
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_mail import Mail, Message

from MLbackend.config import LOGGER
from MLbackend.src.devNetwork import communitySmellsDetector
from MLbackend.src.utils.result import Result
from MLbackend.validations import (
    InvalidInputError,
    validate_email,
    validate_pat,
    validate_url,
)

app = Flask(
    __name__,
    template_folder=os.path.join("..", "frontend", "templates"),
    static_folder=os.path.join("..", "frontend", "static"),
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


@app.route("/api/v1/smells", methods=["POST"])
def detect_smells():
    url = request.form["repo-url"]
    email = request.form["email"]
    pat = request.form["access-token"]

    senti_strength_path: Path = Path(".", "MLbackend", "data")
    output_path: Path = Path(".", "MLbackend", "results")
    result_ins: Result = Result(logger=LOGGER)

    try:
        validate_url(url)
        validate_email(email)
        validate_pat(pat)
        communitySmellsDetector(
            pat=pat,
            repo_url=url,
            senti_strength_path=senti_strength_path,
            output_path=output_path,
            logger=LOGGER,
            result=result_ins,
        )
        if len(result_ins.smells) == 0:
            LOGGER.warning("No community smells detected.")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "No data found, Please try again later",
                    }
                ),
                404,
            )
        global pdf_path
        pdf_path = result_ins.pdf_file_path
        send_email(
            email=email,
            pdf_file_path=result_ins.pdf_file_path,
        )
        return render_template("results.html", data=result_ins.getWebResult())

    except InvalidInputError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        LOGGER.error(f"Unexpected error: {str(e)}")
        LOGGER.error(f"Stack trace:\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Something went wrong."}), 500


@app.route("/api/v1/pdf", methods=["GET"])
def downloadPDF():
    try:
        # Send the generated PDF to the frontend
        pdf_path1 = Path(pdf_path).resolve()
        return send_file(pdf_path1, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(email: str, pdf_file_path: Path) -> None:

    msg = Message(
        subject="Community Smells Detector",
        sender="g01communitysmellsdetector@gmail.com",
        recipients=[email],
    )
    msg.body = "Hey, PFA smells report"
    try:
        with open(pdf_file_path, "rb") as fp:
            msg.attach("smell_report.pdf", "application/pdf", fp.read())
        mail.send(msg)
    except FileNotFoundError:
        LOGGER.error("PDF file not found. Check if the file path is correct.")
    except Exception as e:
        LOGGER.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
