"""صف‌بندی اعلان‌ها (بخش ۸ پلن معماری). این ماژول هرگز مستقیم
SmsProvider/EmailProvider رو صدا نمی‌زنه — فقط سطر تو notification_outbox
می‌نویسه؛ دیسپچر (app/workers/scheduler.py) پردازه‌ی جدا واقعاً ارسال می‌کنه."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.calendar import google_calendar_link
from app.core.persian_date import format_jalali_datetime
from app.models.event import Event, EventSession
from app.models.notification import NotificationChannel, NotificationOutbox, NotificationTemplateKey
from app.models.order import Registration
from app.models.ticket import PricingModel, TicketType
from app.models.user import User


def _event_location(event: Event) -> str:
    return event.venue_address or event.online_platform_name or "آنلاین"


def enqueue(
    db: Session,
    *,
    user: User,
    event_id: int | None,
    template_key: NotificationTemplateKey,
    payload: dict,
) -> list[NotificationOutbox]:
    """برای هر مقصد در دسترس کاربر (موبایل/ایمیل) یه سطر جدا در صف می‌سازه."""
    payload_json = json.dumps(payload, ensure_ascii=False)
    rows: list[NotificationOutbox] = []
    if user.phone:
        rows.append(
            NotificationOutbox(
                user_id=user.id,
                event_id=event_id,
                channel=NotificationChannel.SMS,
                destination=user.phone,
                template_key=template_key,
                payload_json=payload_json,
            )
        )
    if user.email:
        rows.append(
            NotificationOutbox(
                user_id=user.id,
                event_id=event_id,
                channel=NotificationChannel.EMAIL,
                destination=user.email,
                template_key=template_key,
                payload_json=payload_json,
            )
        )
    db.add_all(rows)
    db.commit()
    return rows


def notify_registration_complete(
    db: Session,
    *,
    user: User,
    event: Event,
    session: EventSession,
    ticket_type: TicketType,
    registration: Registration,
) -> list[NotificationOutbox]:
    """بسته به رایگان/پولی‌بودن بلیط، یکی از دو قالب REGISTRATION_COMPLETE /
    TICKET_PURCHASE_COMPLETE رو صف می‌کنه — چون هر دو در واقع همون لحظه‌ی
    complete_order هستن (این پروژه ثبت‌نام جدا از خرید نداره)."""
    template_key = (
        NotificationTemplateKey.REGISTRATION_COMPLETE
        if ticket_type.pricing_model == PricingModel.FREE
        else NotificationTemplateKey.TICKET_PURCHASE_COMPLETE
    )
    location = _event_location(event)
    calendar_link = google_calendar_link(
        title=event.title,
        description=event.description_plain,
        location=location,
        starts_at=session.starts_at,
        duration_minutes=session.duration_minutes,
    )
    payload = {
        "user_name": user.full_name or "",
        "event_title": event.title,
        "session_starts_at_jalali": format_jalali_datetime(session.starts_at),
        "location": location,
        "ticket_code": registration.ticket_code,
        "calendar_link": calendar_link,
        "ticket_type_name": ticket_type.name,
        "ticket_price_formatted": f"{ticket_type.price:,}",
    }
    return enqueue(db, user=user, event_id=event.id, template_key=template_key, payload=payload)


def notify_event_reminder(
    db: Session, *, user: User, event: Event, session: EventSession
) -> list[NotificationOutbox]:
    payload = {
        "user_name": user.full_name or "",
        "event_title": event.title,
        "session_starts_at_jalali": format_jalali_datetime(session.starts_at),
        "location": _event_location(event),
    }
    return enqueue(
        db,
        user=user,
        event_id=event.id,
        template_key=NotificationTemplateKey.EVENT_REMINDER_1H,
        payload=payload,
    )
