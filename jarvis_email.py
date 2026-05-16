import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from livekit.agents import function_tool

load_dotenv()
logger = logging.getLogger(__name__)

@function_tool
async def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email via Gmail."""
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_address or not gmail_password:
        return "Gmail credentials not configured in .env"
    try:
        msg = MIMEMultipart()
        msg["From"] = gmail_address
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, to, msg.as_string())
        logger.info(f"Email sent to {to} | Subject: {subject}")
        return f"Email '{subject}' sent successfully to {to}."
    except smtplib.SMTPAuthenticationError:
        return "Gmail authentication failed. Check App Password."
    except Exception as e:
        logger.exception(f"Email send error: {e}")
        return f"Failed to send email: {e}"