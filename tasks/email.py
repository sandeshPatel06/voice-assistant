"""
Email tasks: compose and send emails securely.
Credentials are read from config.py (environment variables), never hard-coded.
"""

import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_engine import SpeechEngine

from config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

log = logging.getLogger("jarvis.tasks.email")


class EmailTasks:
    """Handle sending emails."""

    def __init__(self, speech: "SpeechEngine") -> None:
        self.speak = speech.speak
        self.listen = speech.listen

    def send_email(self) -> None:
        """Interactive email sending: recipient, subject, body via voice."""
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            self.speak(
                "Email credentials are not configured. "
                "Set JARVIS_EMAIL_ADDRESS and JARVIS_EMAIL_PASSWORD in your environment."
            )
            return

        self.speak("Who should I send the email to?")
        recipient = self.listen()
        if recipient == "None":
            self.speak("No recipient provided.")
            return

        # Basic email validation
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", recipient):
            self.speak("That doesn't look like a valid email address.")
            return

        self.speak("What is the subject?")
        subject = self.listen()
        if subject == "None":
            subject = ""

        self.speak("What should I say in the email?")
        body = self.listen()
        if body == "None":
            self.speak("No message body. Cancelling.")
            return

        try:
            self.speak("Sending email...")
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
            server.quit()

            self.speak("Email sent successfully!")
        except Exception:
            log.exception("Failed to send email")
            self.speak("I'm sorry, I could not send the email.")
