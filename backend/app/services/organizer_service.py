"""پروفایل عمومی برگزارکننده — مشابه instructor_service.py، برای صفحه‌ی
عمومی برگزارکننده (کلیک از /follows یا هر جای دیگه‌ای که اسم برگزارکننده
نشون داده می‌شه)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus, EventVisibility
from app.services.event_service import event_query


def organizer_published_events(db: Session, organizer_id: int) -> list[Event]:
    return (
        event_query(db)
        .filter(
            Event.organizer_id == organizer_id,
            Event.status == EventStatus.PUBLISHED,
            Event.visibility == EventVisibility.PUBLIC,
        )
        .order_by(Event.published_at.desc())
        .all()
    )
