"""Email notification channel — sends documents via SMTP."""

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.config.settings import settings
from src.notifications.router import NotificationChannel

logger = logging.getLogger("primeev.notifications.email")


class EmailChannel(NotificationChannel):
    """Sends notifications via SMTP email with optional PDF attachment."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 1025,
        from_address: str = "factory-agent@primeev.com",
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
    ):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._from_address = from_address
        self._username = username
        self._password = password
        self._use_tls = use_tls

    @property
    def name(self) -> str:
        return "email"

    def send(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachment_path: Path | None = None,
    ) -> bool:
        msg = MIMEMultipart()
        msg["From"] = self._from_address
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <div style="background: #0284c7; color: white; padding: 12px 20px; border-radius: 4px 4px 0 0;">
                <strong>PrimeEV Motors — Factory Floor Agent</strong>
            </div>
            <div style="padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
                <p>{body}</p>
                {'<p style="color: #666; font-size: 12px;">PDF report attached.</p>' if attachment_path else ''}
            </div>
            <div style="padding: 10px 20px; font-size: 11px; color: #999;">
                This notification was generated automatically by the PrimeEV Factory Floor Agent.
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        if attachment_path and attachment_path.exists():
            with open(attachment_path, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition", "attachment",
                    filename=attachment_path.name,
                )
                msg.attach(attachment)

        try:
            if self._use_tls:
                server = smtplib.SMTP(self._smtp_host, self._smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self._smtp_host, self._smtp_port)

            if self._username and self._password:
                server.login(self._username, self._password)

            server.sendmail(self._from_address, recipients, msg.as_string())
            server.quit()
            logger.info("Email sent to %s: %s", recipients, subject)
            return True

        except ConnectionRefusedError:
            logger.warning(
                "SMTP server not available at %s:%d — email not sent. "
                "For local testing, run: python -m smtpd -n -c DebuggingServer localhost:1025",
                self._smtp_host, self._smtp_port,
            )
            return False
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False
