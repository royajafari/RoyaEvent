from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class EventVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class EventFormat(str, enum.Enum):
    ONLINE = "online"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


event_tags = Table(
    "event_tags",
    Base.metadata,
    Column("event_id", ForeignKey("events.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

event_instructors = Table(
    "event_instructors",
    Base.metadata,
    Column("event_id", ForeignKey("events.id"), primary_key=True),
    Column("instructor_id", ForeignKey("instructors.id"), primary_key=True),
)


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    event_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description_plain: Mapped[str] = mapped_column(Text, nullable=False, default="")
    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    promo_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)

    visibility: Mapped[EventVisibility] = mapped_column(
        Enum(EventVisibility), default=EventVisibility.PUBLIC, nullable=False
    )
    private_access_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    format: Mapped[EventFormat] = mapped_column(Enum(EventFormat), nullable=False)
    venue_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    online_platform_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.DRAFT, nullable=False)
    is_featured: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_instant_registration: Mapped[bool] = mapped_column(default=False, nullable=False)
    refund_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    sales_open_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    category = relationship("Category")
    organizer = relationship("User")
    sessions: Mapped[list[EventSession]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="EventSession.starts_at"
    )
    tags = relationship("Tag", secondary=event_tags)
    instructors = relationship("Instructor", secondary=event_instructors)

    @property
    def organizer_name(self) -> str | None:
        if self.organizer is None:
            return None
        return self.organizer.full_name or self.organizer.phone or self.organizer.email


class EventSession(Base, TimestampMixin):
    """هر رویداد حداقل یک جلسه دارد (تک‌جلسه‌ای = count==1)."""

    __tablename__ = "event_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    venue_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    online_join_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    event: Mapped[Event] = relationship(back_populates="sessions")
