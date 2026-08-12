from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """UTC ساده (بدون tzinfo) — SQLite نوع timezone-aware واقعی ندارد و
    مقایسه‌ی aware/naive استثنا می‌اندازد؛ برای ثبات، همه‌جا naive UTC
    ذخیره و مقایسه می‌شود."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), default=utcnow, onupdate=utcnow, nullable=False
    )
