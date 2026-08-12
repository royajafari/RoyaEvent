import logging

import httpx

from app.providers.email.base import EmailProvider, EmailSendResult

logger = logging.getLogger("royaevent.email.resend")

RESEND_SEND_URL = "https://api.resend.com/emails"


class ResendProvider(EmailProvider):
    """Provider جایگزین ایمیل. https://resend.com/docs/api-reference/emails/send-email"""

    name = "resend"

    def __init__(self, api_key: str, sender_email: str, sender_name: str):
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name

    def send(self, to_email: str, subject: str, html_content: str) -> EmailSendResult:
        try:
            response = httpx.post(
                RESEND_SEND_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": f"{self.sender_name} <{self.sender_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return EmailSendResult(provider=self.name, provider_message_id=data.get("id"), success=True)
        except httpx.HTTPError:
            logger.exception("Resend email send failed for to_email=%s", to_email)
            return EmailSendResult(provider=self.name, provider_message_id=None, success=False)
