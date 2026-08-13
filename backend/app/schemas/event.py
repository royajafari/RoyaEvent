from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int | None

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class EventSessionIn(BaseModel):
    starts_at: datetime
    duration_minutes: int = Field(gt=0, le=1440)
    venue_address: str | None = None
    online_join_url: str | None = None
    capacity: int | None = Field(default=None, gt=0)


class EventSessionOut(BaseModel):
    id: int
    starts_at: datetime
    duration_minutes: int
    sequence_order: int
    venue_address: str | None
    online_join_url: str | None
    capacity: int | None

    model_config = {"from_attributes": True}


class InstructorRefOut(BaseModel):
    """نسخه‌ی سبک مدرس برای جاسازی داخل EventDetailOut — بدون follower_count/bio."""

    id: int
    name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class EventCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1)
    category_id: int
    format: Literal["online", "in_person", "hybrid"]
    venue_address: str | None = None
    online_platform_name: str | None = None
    visibility: Literal["public", "private"] = "public"
    refund_policy: str | None = None
    tag_names: list[str] = Field(default_factory=list, max_length=10)
    instructor_names: list[str] = Field(default_factory=list, max_length=10)
    sessions: list[EventSessionIn] = Field(min_length=1)

    @field_validator("sessions")
    @classmethod
    def sessions_not_empty(cls, v: list[EventSessionIn]) -> list[EventSessionIn]:
        if not v:
            raise ValueError("هر رویداد باید حداقل یک جلسه داشته باشد")
        return v

    @field_validator("venue_address")
    @classmethod
    def venue_required_for_in_person(cls, v, info):
        fmt = info.data.get("format")
        if fmt in ("in_person", "hybrid") and not v:
            raise ValueError("برای رویداد حضوری/ترکیبی، آدرس محل برگزاری الزامی است")
        return v


class EventUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    category_id: int | None = None
    format: Literal["online", "in_person", "hybrid"] | None = None
    venue_address: str | None = None
    online_platform_name: str | None = None
    refund_policy: str | None = None
    tag_names: list[str] | None = Field(default=None, max_length=10)
    instructor_names: list[str] | None = Field(default=None, max_length=10)


class EventListItemOut(BaseModel):
    id: int
    title: str
    slug: str
    event_code: str
    banner_url: str | None
    category: CategoryOut | None
    format: str
    status: str
    is_featured: bool
    rating_avg: float
    rating_count: int
    view_count: int
    next_session_at: datetime | None

    model_config = {"from_attributes": True}


class EventDetailOut(BaseModel):
    id: int
    organizer_id: int
    organizer_name: str | None = None
    title: str
    slug: str
    event_code: str
    description: str
    banner_url: str | None
    promo_video_url: str | None
    category: CategoryOut | None
    visibility: str
    format: str
    venue_address: str | None
    online_platform_name: str | None
    status: str
    is_featured: bool
    refund_policy: str | None
    rating_avg: float
    rating_count: int
    view_count: int
    published_at: datetime | None
    sessions: list[EventSessionOut]
    tags: list[TagOut]
    instructors: list[InstructorRefOut]

    model_config = {"from_attributes": True}
