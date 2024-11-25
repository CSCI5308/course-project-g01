from flask import Flask


def configure_app(app: Flask):
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USERNAME"] = "g01communitysmellsdetector@gmail.com"
    app.config["MAIL_PASSWORD"] = "gmki hznr hixx bihb"
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
