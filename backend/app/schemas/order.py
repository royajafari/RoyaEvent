from datetime import datetime

from pydantic import BaseModel


class OrderCreateIn(BaseModel):
    ticket_type_id: int
    session_id: int
    discount_code: str | None = None


class OrderOut(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: str
    subtotal: int
    discount_amount: int
    total: int
    payment_status: str
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RegistrationOut(BaseModel):
    id: int
    event_id: int
    session_id: int
    status: str
    ticket_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MyTicketOut(BaseModel):
    registration: RegistrationOut
    event_title: str
    event_slug: str
    event_format: str
    session_starts_at: datetime
    session_duration_minutes: int
    session_online_join_url: str | None
    session_venue_address: str | None

    model_config = {"from_attributes": True}
