import logging
from uuid import uuid4

from app.providers.email.base import EmailProvider, EmailSendResult

logger = logging.getLogger("royaevent.email.console")


class ConsoleEmailProvider(EmailProvider):
    """Provider توسعه/تست: به‌جای ارسال واقعی، فقط لاگ می‌کند."""

    name = "console"

    def __init__(self):
        self.sent_messages: list[dict] = []

    def send(self, to_email: str, subject: str, html_content: str) -> EmailSendResult:
        message_id = uuid4().hex
        logger.info(
            "[Email:console] to=%s id=%s subject=%s body=%s",
            to_email,
            message_id,
            subject,
            html_content,
        )
        self.sent_messages.append(
            {"to": to_email, "id": message_id, "subject": subject, "html": html_content}
        )
        return EmailSendResult(provider=self.name, provider_message_id=message_id, success=True)
