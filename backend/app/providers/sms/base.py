from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SmsSendResult:
    provider: str
    provider_message_id: str | None
    success: bool


class SmsProvider(ABC):
    """اینترفیس مشترک ارسال پیامک — Business logic هرگز مستقیماً IPPanel/Kavenegar را صدا نمی‌زند."""

    name: str

    @abstractmethod
    def send(self, destination: str, message: str) -> SmsSendResult: ...
