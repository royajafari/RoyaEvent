from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.event import Event
from app.models.ticket import TicketType
from app.schemas.ticket import TicketTypeIn, TicketTypeOut


class TicketServiceError(ValueError):
    pass


def is_early_bird_active(event: Event) -> bool:
    """طبق نیازمندی ۳۴ پلن: اگر کمتر از یک‌سوم بازه‌ی (شروع فروش تا شروع
    رویداد) گذشته باشد، بلیط زودهنگام فعال است. مرجع «شروع رویداد» اولین
    جلسه است (برای رویدادهای چندجلسه‌ای ساده‌سازی معقول)."""
    if not event.sessions:
        return False
    window_start = event.sales_open_at or event.published_at
    if window_start is None:
        return False

    first_session_start = min(s.starts_at for s in event.sessions)
    if first_session_start <= window_start:
        return False

    window = first_session_start - window_start
    elapsed = utcnow() - window_start
    return elapsed < window / 3


def create_ticket_type(db: Session, event: Event, data: TicketTypeIn) -> TicketType:
    price = data.price if data.pricing_model == "paid" else 0
    ticket_type = TicketType(
        event_id=event.id,
        name=data.name,
        price=price,
        pricing_model=data.pricing_model,
        quantity_total=data.quantity_total,
        is_early_bird=data.is_early_bird,
    )
    db.add(ticket_type)
    db.commit()
    db.refresh(ticket_type)
    return ticket_type


def to_ticket_type_out(ticket_type: TicketType, event: Event) -> TicketTypeOut:
    is_sold_out = (
        ticket_type.quantity_total is not None
        and ticket_type.quantity_sold >= ticket_type.quantity_total
    )
    return TicketTypeOut(
        id=ticket_type.id,
        event_id=ticket_type.event_id,
        name=ticket_type.name,
        price=ticket_type.price,
        pricing_model=ticket_type.pricing_model.value,
        quantity_total=ticket_type.quantity_total,
        quantity_sold=ticket_type.quantity_sold,
        is_early_bird=ticket_type.is_early_bird,
        is_sold_out=is_sold_out,
        is_early_bird_active=is_early_bird_active(event) if ticket_type.is_early_bird else False,
    )
