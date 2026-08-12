import logging

import httpx

from app.providers.sms.base import SmsProvider, SmsSendResult

logger = logging.getLogger("royaevent.sms.ippanel")

# نکته: این پیاده‌سازی بر اساس API عمومی/متداول "webservice send" ادج IPPanel
# نوشته شده. قبل از استفاده‌ی واقعی در production، حتماً این endpoint و شکل
# payload را با پنل و مستندات فعلی حساب IPPanel خودتان تطبیق بدهید — ممکن
# است لازم باشد به‌جای ارسال متن آزاد، از یک Pattern/OTP از پیش تأییدشده
# در پنل استفاده کنید (طبق چک‌لیست فاز ۱ سند OTP: «بررسی Pattern/OTP»).
IPPANEL_SEND_URL = "https://edge.ippanel.com/v1/api/send"


class IPPanelProvider(SmsProvider):
    name = "ippanel"

    def __init__(self, api_key: str, sender_number: str):
        self.api_key = api_key
        self.sender_number = sender_number

    def send(self, destination: str, message: str) -> SmsSendResult:
        try:
            response = httpx.post(
                IPPANEL_SEND_URL,
                headers={"Authorization": self.api_key},
                json={
                    "sending_type": "webservice",
                    "from_number": self.sender_number,
                    "message": message,
                    "params": {"recipients": [destination]},
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            message_id = str(data.get("data", {}).get("message_id") or data.get("data"))
            return SmsSendResult(provider=self.name, provider_message_id=message_id, success=True)
        except httpx.HTTPError:
            logger.exception("IPPanel SMS send failed for destination=%s", destination)
            return SmsSendResult(provider=self.name, provider_message_id=None, success=False)
