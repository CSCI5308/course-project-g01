from flask import Flask, render_template, request, jsonify, send_file
from community_smells import detect_community_smells
from email_utils import send_email, create_pdf, configure_app
from MLbackend.validations import validate_input

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
        return render_template("results.html", data=result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/v1/pdf", methods=["GET"])
def generate_pdf():
    try:
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

        PDF_FILE_PATH = res
        return send_file(PDF_FILE_PATH, as_attachment=True)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
