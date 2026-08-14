from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, utcnow


class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"


class NotificationTemplateKey(str, enum.Enum):
    REGISTRATION_COMPLETE = "registration_complete"
    TICKET_PURCHASE_COMPLETE = "ticket_purchase_complete"
    EVENT_REMINDER_1H = "event_reminder_1h"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationOutbox(Base, TimestampMixin):
    """صف مشترک ۳ قالب اعلان (بخش ۸ پلن معماری) — دیسپچر (app/workers/scheduler.py)
    هر چند ثانیه این جدول رو می‌خونه و از طریق SmsProvider/EmailProvider ارسال
    می‌کنه؛ NotificationService هرگز مستقیم provider رو صدا نمی‌زنه."""

    __tablename__ = "notification_outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True, index=True)

    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    template_key: Mapped[NotificationTemplateKey] = mapped_column(
        Enum(NotificationTemplateKey), nullable=False
    )
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False, index=True)

    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
