from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.core.permissions import require_event_owner
from app.models.event import Event
from app.models.ticket import DiscountCode, PlatformDiscountCode, TicketType
from app.models.user import User
from app.schemas.ticket import (
    DiscountCodeIn,
    DiscountCodeOut,
    DiscountValidateIn,
    TicketTypeIn,
    TicketTypeOut,
)
from app.services import ticket_service
from app.services.discount_service import find_valid_discount

router = APIRouter(tags=["tickets"])


def _get_owned_event(db: Session, event_id: int, user: User) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    require_event_owner(event, user)
    return event


@router.get("/events/{event_id}/ticket-types", response_model=list[TicketTypeOut])
def list_ticket_types(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    ticket_types = db.query(TicketType).filter_by(event_id=event_id).all()
    return [ticket_service.to_ticket_type_out(t, event) for t in ticket_types]


@router.post(
    "/events/{event_id}/ticket-types", response_model=TicketTypeOut, status_code=status.HTTP_201_CREATED
)
def create_ticket_type(
    event_id: int,
    body: TicketTypeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_owned_event(db, event_id, current_user)
    ticket_type = ticket_service.create_ticket_type(db, event, body)
    return ticket_service.to_ticket_type_out(ticket_type, event)


@router.post(
    "/events/{event_id}/discount-codes",
    response_model=DiscountCodeOut,
    status_code=status.HTTP_201_CREATED,
)
def create_event_discount_code(
    event_id: int,
    body: DiscountCodeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_event(db, event_id, current_user)
    code = DiscountCode(
        event_id=event_id,
        code=body.code,
        discount_type=body.discount_type,
        value=body.value,
        max_uses=body.max_uses,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
    )
    db.add(code)
    db.commit()
    db.refresh(code)
    return code


@router.post(
    "/admin/discount-codes", response_model=DiscountCodeOut, status_code=status.HTTP_201_CREATED
)
def create_platform_discount_code(
    body: DiscountCodeIn,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    code = PlatformDiscountCode(
        code=body.code,
        discount_type=body.discount_type,
        value=body.value,
        max_uses=body.max_uses,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        created_by=current_admin.id,
    )
    db.add(code)
    db.commit()
    db.refresh(code)
    return code


@router.post("/discount-codes/validate")
def validate_discount_code(body: DiscountValidateIn, db: Session = Depends(get_db)):
    record = find_valid_discount(db, body.event_id, body.code)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "کد تخفیف نامعتبر یا منقضی‌شده است")
    return {
        "valid": True,
        "discount_type": record.discount_type.value,
        "value": record.value,
    }
