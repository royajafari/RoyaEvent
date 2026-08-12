from functools import lru_cache

from app.core.config import get_settings
from app.providers.email.base import EmailProvider
from app.providers.email.brevo import BrevoProvider
from app.providers.email.console import ConsoleEmailProvider
from app.providers.email.resend import ResendProvider


@lru_cache
def get_email_provider() -> EmailProvider:
    settings = get_settings()

    if settings.email_provider == "brevo" and settings.brevo_api_key:
        return BrevoProvider(
            settings.brevo_api_key, settings.brevo_sender_email, settings.brevo_sender_name
        )
    if settings.email_provider == "resend" and settings.resend_api_key:
        return ResendProvider(
            settings.resend_api_key, settings.brevo_sender_email, settings.brevo_sender_name
        )

    return ConsoleEmailProvider()
