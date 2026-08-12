from functools import lru_cache

from app.core.config import get_settings
from app.providers.sms.base import SmsProvider
from app.providers.sms.console import ConsoleSmsProvider
from app.providers.sms.ippanel import IPPanelProvider
from app.providers.sms.kavenegar import KavenegarProvider


@lru_cache
def get_sms_provider() -> SmsProvider:
    settings = get_settings()

    if settings.sms_provider == "ippanel" and settings.ippanel_api_key:
        return IPPanelProvider(settings.ippanel_api_key, settings.ippanel_sender_number)
    if settings.sms_provider == "kavenegar" and settings.kavenegar_api_key:
        return KavenegarProvider(settings.kavenegar_api_key, settings.kavenegar_sender)

    # بدون API key معتبر، به‌صورت خودکار روی provider توسعه/تست می‌افتیم
    # تا محیط dev/CI بدون اعتبار واقعی هم کار کند.
    return ConsoleSmsProvider()
