import os
import re
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from livekit.agents import function_tool

load_dotenv()
logger = logging.getLogger(__name__)

# BUG FIX: original read GMAIL_ADDRESS / GMAIL_APP_PASSWORD but the README
# tells users to set EMAIL / EMAIL_PASSWORD in their .env — so credentials
# were always None and every send call silently failed. Both names are now
# supported; EMAIL / EMAIL_PASSWORD take priority for README compatibility.
def _get_credentials():
    address  = os.getenv("EMAIL") or os.getenv("GMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
    return address, password

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@function_tool
async def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email via Gmail.

    Args:
        to (str): Recipient email address.
        subject (str): Email subject line.
        body (str): Plain-text email body.
    """
    # BUG FIX: validate recipient address before hitting SMTP.
    if not _EMAIL_RE.match(to):
        return f"❌ Invalid email address: '{to}'. Please provide a valid address."

    gmail_address, gmail_password = _get_credentials()

    if not gmail_address or not gmail_password:
        return (
            "Gmail credentials not configured. "
            "Add EMAIL and EMAIL_PASSWORD to your .env file."
        )

    try:
        msg = MIMEMultipart()
        msg["From"]    = gmail_address
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, to, msg.as_string())

        logger.info(f"Email sent to {to} | Subject: {subject}")
        return f"Email '{subject}' sent successfully to {to}."

    except smtplib.SMTPAuthenticationError:
        return (
            "Gmail authentication failed. "
            "Make sure you are using an App Password (not your account password). "
            "See: https://support.google.com/accounts/answer/185833"
        )
    except smtplib.SMTPRecipientsRefused:
        return f"Recipient '{to}' was refused by the server."
    except Exception as e:
        logger.exception(f"Email send error: {e}")
        return f"Failed to send email: {e}"
