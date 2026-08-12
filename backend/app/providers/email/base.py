from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailSendResult:
    provider: str
    provider_message_id: str | None
    success: bool


class EmailProvider(ABC):
    """اینترفیس مشترک ارسال ایمیل — Business logic هرگز مستقیماً Brevo/Resend را صدا نمی‌زند."""

    name: str

    @abstractmethod
    def send(self, to_email: str, subject: str, html_content: str) -> EmailSendResult: ...
