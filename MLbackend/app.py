from datetime import datetime
from flask import Flask, render_template, request, jsonify
import logging
from logging import Logger
from pathlib import Path
import re
import validators
from src.devNetwork import communitySmellsDetector

LOG_FOLDER_PATH: Path = Path(".", "logs")
time_now = datetime.now()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=Path(".", "logs", time_now.strftime("log_%Y-%m-%d_%H-%M-%S.log")),
)

LOGGER: Logger = logging.getLogger(__name__)

app = Flask(__name__)


class InvalidInputError(Exception):
    pass


def validate_repo_url(url: str) -> None:

    if not url or not validators.url(url):
        LOGGER.error(f"Invalid repository URL format {url}.")
        raise InvalidInputError("Invalid repository URL format.")


def validate_email(email: str) -> None:

    if not email or not validators.email(email):
        LOGGER.error(f"Invalid Email format {email}.")
        raise InvalidInputError("Invalid email format.")


def validate_pat(token: str) -> None:

    if not re.match(r"^[a-zA-Z0-9-_]+$", token):
        LOGGER.error(f"Invalid PAT format {token}.")
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

    try:
        # Call the function and save the result
        result = communitySmellsDetector(
            pat, repo_url, senti_strength_path, output_path, LOGGER
        )
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
        return render_template("results.html", data=result)

    except Exception:
        # Handle unexpected errors
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Something went wrong. Please try again later",
                }
            ),
            500,
        )  # Internal Server Error


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
