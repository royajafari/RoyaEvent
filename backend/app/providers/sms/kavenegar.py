import logging

import httpx

from app.providers.sms.base import SmsProvider, SmsSendResult

logger = logging.getLogger("royaevent.sms.kavenegar")


class KavenegarProvider(SmsProvider):
    """Provider جایگزین طبق سند OTP. https://kavenegar.com/rest.html"""

    name = "kavenegar"

    def __init__(self, api_key: str, sender: str = ""):
        self.api_key = api_key
        self.sender = sender

    def send(self, destination: str, message: str) -> SmsSendResult:
        url = f"https://api.kavenegar.com/v1/{self.api_key}/sms/send.json"
        params = {"receptor": destination, "message": message}
        if self.sender:
            params["sender"] = self.sender
        try:
            response = httpx.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            entries = data.get("entries") or []
            message_id = str(entries[0]["messageid"]) if entries else None
            return SmsSendResult(provider=self.name, provider_message_id=message_id, success=True)
        except httpx.HTTPError:
            logger.exception("Kavenegar SMS send failed for destination=%s", destination)
            return SmsSendResult(provider=self.name, provider_message_id=None, success=False)
