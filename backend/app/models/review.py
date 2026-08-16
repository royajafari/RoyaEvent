from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class ReviewStatus(str, enum.Enum):
    PUBLISHED = "published"
    HIDDEN = "hidden"


class EventReview(Base, TimestampMixin):
    """نظر ۴محوره — بخش ۳ پلن معماری. تصمیم کاربر: این خودِ منبع
    events.rating_avg است، نه یه مکانیزم امتیازدهی جدا (برخلاف مدرس/
    برگزارکننده/سایت که فقط یه امتیاز ساده‌ی ۱-۵ دارن، بدون محور)."""

    __tablename__ = "event_reviews"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_event_review_user_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id"), nullable=False)

    axis_content_uptodate: Mapped[int] = mapped_column(Integer, nullable=False)
    axis_instructor_mastery: Mapped[int] = mapped_column(Integer, nullable=False)
    axis_value_for_price: Mapped[int] = mapped_column(Integer, nullable=False)
    axis_experience_driven: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_computed: Mapped[float] = mapped_column(Float, nullable=False)

    comment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.PUBLISHED, nullable=False
    )
    hidden_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
