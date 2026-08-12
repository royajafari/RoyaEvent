from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class Favorite(Base, TimestampMixin):
    """هم علاقه‌مندی و هم «مارک‌کردن» — یک مکانیزم واحد (بخش ۱۵ پلن)."""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_favorite_user_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)


class OrganizerFollow(Base, TimestampMixin):
    __tablename__ = "organizer_follows"
    __table_args__ = (
        UniqueConstraint("follower_user_id", "organizer_id", name="uq_follow_user_organizer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    follower_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class InstructorFollow(Base, TimestampMixin):
    __tablename__ = "instructor_follows"
    __table_args__ = (
        UniqueConstraint("follower_user_id", "instructor_id", name="uq_follow_user_instructor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    follower_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("instructors.id"), nullable=False, index=True)
