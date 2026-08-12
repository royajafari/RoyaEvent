import logging
from uuid import uuid4

from app.providers.sms.base import SmsProvider, SmsSendResult

logger = logging.getLogger("royaevent.sms.console")


class ConsoleSmsProvider(SmsProvider):
    """Provider توسعه/تست: به‌جای ارسال واقعی، فقط لاگ می‌کند.

    وقتی API key واقعی IPPanel/Kavenegar تنظیم نشده باشد به‌صورت خودکار
    انتخاب می‌شود (app/providers/sms/factory.py) تا توسعه‌ی محلی و تست
    بدون نیاز به اعتبار واقعی ممکن باشد. OTP هرگز در لاگ‌های production
    نباید ثبت شود — این provider فقط برای dev/test است.
    """

    name = "console"

    def __init__(self):
        # پیام‌های ارسال‌شده در حافظه نگه داشته می‌شوند تا تست‌ها بتوانند
        # OTP واقعی را بدون parse کردن متن لاگ بخوانند.
        self.sent_messages: list[dict] = []

    def send(self, destination: str, message: str) -> SmsSendResult:
        message_id = uuid4().hex
        logger.info("[SMS:console] to=%s id=%s message=%s", destination, message_id, message)
        self.sent_messages.append({"to": destination, "id": message_id, "message": message})
        return SmsSendResult(provider=self.name, provider_message_id=message_id, success=True)
