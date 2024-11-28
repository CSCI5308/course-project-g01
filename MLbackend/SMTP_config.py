from dotenv import load_dotenv
import os


load_dotenv()


email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')


def configure_app(app):
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USERNAME"] = email
    app.config["MAIL_PASSWORD"] = password
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
