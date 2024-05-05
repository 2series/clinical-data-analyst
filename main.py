import os
import logging

from flask import Flask, render_template
from gunicorn.app.base import BaseApplication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("index.html", section="about")

@app.route("/services")
def services():
    return render_template("index.html", section="services")

@app.route("/contact")
def contact():
    return render_template("index.html", section="contact")

@app.route("/send-message", methods=['POST'])
def send_message():
    from flask import request
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    # Environment variables for email functionality
    # These variables are fetched from the environment and not linked directly to HTML
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('SENDER_PASSWORD')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    
    if not sender_email or not sender_password or not receiver_email:
        logger.error("Email environment variables are not set.")
        return "Internal server error. Please try again later.", 500
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"New message from {name} via Contact Form"
    
    body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            logger.info(f"Message sent from {name} ({email}): {message}")
            return "Message sent successfully!", 200
    except smtplib.SMTPAuthenticationError:
        logger.error("Failed to authenticate with the SMTP server. Check the SENDER_EMAIL and SENDER_PASSWORD.")
        return "Authentication failed. Please check the application settings.", 500
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return "Failed to send message. Please try again later.", 500


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.application = app
        self.options = options or {}
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


# Do not remove the main function while updating the app.
if __name__ == "__main__":
    options = {"bind": "%s:%s" % ("0.0.0.0", "8080"), "workers": 4, "loglevel": "info", "accesslog": "-"}
    StandaloneApplication(app, options).run()
