from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin

# امتیاز مدرس/برگزارکننده/سایت — ضربه‌ی ساده‌ی ۱-۵ ستاره، بدون محور
# (برخلاف EventReview که ۴محوره است). سه جدول جدا به‌جای یک جدول
# پلی‌مورفیک، به‌خاطر یکپارچگی FK واقعی در SQLite (تصمیم #۸ پلن معماری).


class InstructorRating(Base, TimestampMixin):
    __tablename__ = "instructor_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "instructor_id", name="uq_instructor_rating_user_instructor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("instructors.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)


class OrganizerRating(Base, TimestampMixin):
    __tablename__ = "organizer_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "organizer_id", name="uq_organizer_rating_user_organizer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)


class PlatformRating(Base, TimestampMixin):
    __tablename__ = "platform_ratings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_platform_rating_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
