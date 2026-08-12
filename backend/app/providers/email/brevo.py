import logging

import httpx

from app.providers.email.base import EmailProvider, EmailSendResult

logger = logging.getLogger("royaevent.email.brevo")

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoProvider(EmailProvider):
    """https://developers.brevo.com/docs/send-a-transactional-email"""

    name = "brevo"

    def __init__(self, api_key: str, sender_email: str, sender_name: str):
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name

    def send(self, to_email: str, subject: str, html_content: str) -> EmailSendResult:
        try:
            response = httpx.post(
                BREVO_SEND_URL,
                headers={
                    "api-key": self.api_key,
                    "content-type": "application/json",
                    "accept": "application/json",
                },
                json={
                    "sender": {"name": self.sender_name, "email": self.sender_email},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "htmlContent": html_content,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return EmailSendResult(
                provider=self.name, provider_message_id=data.get("messageId"), success=True
            )
        except httpx.HTTPError:
            logger.exception("Brevo email send failed for to_email=%s", to_email)
            return EmailSendResult(provider=self.name, provider_message_id=None, success=False)
