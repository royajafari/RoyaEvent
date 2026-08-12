from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class OTPChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"


class OTPPurpose(str, enum.Enum):
    LOGIN = "login"
    ADD_CONTACT_CHANNEL = "add_contact_channel"


class OTPStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    LOCKED = "locked"
    CANCELLED = "cancelled"


class OTPChallenge(Base, TimestampMixin):
    """طبق docs/event_otp_email_sms_plan_fa.md، بخش ۱۵ — بدون تغییر در مکانیزم."""

    __tablename__ = "otp_challenge"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    event_id: Mapped[int | None] = mapped_column(nullable=True)

    destination: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    channel: Mapped[OTPChannel] = mapped_column(Enum(OTPChannel), nullable=False)
    purpose: Mapped[OTPPurpose] = mapped_column(Enum(OTPPurpose), nullable=False)

    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OTPStatus] = mapped_column(Enum(OTPStatus), default=OTPStatus.PENDING, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    request_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
