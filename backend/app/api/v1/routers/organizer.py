import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import require_event_owner
from app.models.event import Event, EventSession
from app.models.order import OrderItem, Registration
from app.models.ticket import TicketType
from app.models.user import User
from app.schemas.organizer import AttendeeOut
from app.services.order_service import OrderServiceError, cancel_registration

router = APIRouter(prefix="/organizer", tags=["organizer"])


def _get_owned_event(db: Session, event_id: int, user: User) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    require_event_owner(event, user)
    return event


def _attendee_rows(db: Session, event_id: int) -> list[AttendeeOut]:
    registrations = db.query(Registration).filter_by(event_id=event_id).all()
    rows = []
    for reg in registrations:
        user = db.get(User, reg.user_id)
        session = db.get(EventSession, reg.session_id)
        order_item = db.get(OrderItem, reg.order_item_id)
        ticket_type = db.get(TicketType, order_item.ticket_type_id) if order_item else None
        rows.append(
            AttendeeOut(
                registration_id=reg.id,
                user_id=reg.user_id,
                user_full_name=user.full_name if user else None,
                user_phone=user.phone if user else None,
                user_email=user.email if user else None,
                session_starts_at=session.starts_at,
                ticket_type_name=ticket_type.name if ticket_type else "",
                status=reg.status.value,
                ticket_code=reg.ticket_code,
                created_at=reg.created_at,
            )
        )
    return rows


@router.get("/events/{event_id}/attendees", response_model=list[AttendeeOut])
def list_attendees(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _get_owned_event(db, event_id, current_user)
    return _attendee_rows(db, event_id)


@router.delete("/events/{event_id}/attendees/{registration_id}", response_model=AttendeeOut)
def remove_attendee(
    event_id: int,
    registration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_event(db, event_id, current_user)
    registration = db.get(Registration, registration_id)
    if registration is None or registration.event_id != event_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ثبت‌نام یافت نشد")

    try:
        cancel_registration(db, registration)
    except OrderServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    updated_rows = _attendee_rows(db, event_id)
    return next(r for r in updated_rows if r.registration_id == registration_id)


@router.get("/events/{event_id}/attendees/export")
def export_attendees_csv(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = _get_owned_event(db, event_id, current_user)
    rows = _attendee_rows(db, event_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["نام", "موبایل", "ایمیل", "زمان جلسه", "نوع بلیط", "وضعیت", "کد بلیط", "تاریخ ثبت‌نام"]
    )
    for row in rows:
        writer.writerow(
            [
                row.user_full_name or "",
                row.user_phone or "",
                row.user_email or "",
                row.session_starts_at.isoformat(),
                row.ticket_type_name,
                row.status,
                row.ticket_code,
                row.created_at.isoformat(),
            ]
        )

    buffer.seek(0)
    filename = f"attendees-{event.event_code}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
