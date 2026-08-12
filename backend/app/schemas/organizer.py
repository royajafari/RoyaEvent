from datetime import datetime

from pydantic import BaseModel


class AttendeeOut(BaseModel):
    registration_id: int
    user_id: int
    user_full_name: str | None
    user_phone: str | None
    user_email: str | None
    session_starts_at: datetime
    ticket_type_name: str
    status: str
    ticket_code: str
    created_at: datetime
