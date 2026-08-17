from datetime import datetime

from pydantic import BaseModel, Field


class AdminEventOut(BaseModel):
    id: int
    title: str
    slug: str
    event_code: str
    status: str
    is_featured: bool
    organizer_id: int
    organizer_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeatureToggleIn(BaseModel):
    is_featured: bool


class DeleteEventIn(BaseModel):
    reason: str | None = None


class AdminUserOut(BaseModel):
    id: int
    phone: str | None
    email: str | None
    full_name: str | None
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SuspendUserIn(BaseModel):
    suspended: bool
    reason: str | None = None


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None


class AuditLogEntryOut(BaseModel):
    id: int
    admin_user_id: int
    admin_name: str | None
    action: str
    target_type: str
    target_id: int
    reason: str | None
    created_at: datetime


class AdminReviewOut(BaseModel):
    id: int
    event_id: int
    event_title: str
    user_id: int
    user_name: str | None
    overall_computed: float
    comment_text: str | None
    status: str
    hidden_reason: str | None
    created_at: datetime


class HideReviewIn(BaseModel):
    hidden: bool
    reason: str | None = None


class AdminNotificationOut(BaseModel):
    id: int
    channel: str
    destination: str
    template_key: str
    status: str
    attempts: int
    provider: str | None
    last_error: str | None
    event_id: int | None
    event_title: str | None
    created_at: datetime
