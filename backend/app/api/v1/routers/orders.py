from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.calendar import google_calendar_link
from app.core.permissions import require_complete_profile
from app.core.rate_limit_middleware import limiter
from app.models.event import Event, EventSession
from app.models.order import Order, Registration
from app.models.user import User
from app.schemas.order import MyTicketOut, OrderCreateIn, OrderOut, RegistrationOut
from app.services.order_service import OrderServiceError, cancel_registration, complete_order, create_order

router = APIRouter(tags=["orders"])


def _get_owned_order(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "سفارش یافت نشد")
    if order.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "این سفارش متعلق به شما نیست")
    return order


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_order_endpoint(
    request: Request,
    body: OrderCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_complete_profile(current_user)
    try:
        return create_order(db, current_user.id, body)
    except OrderServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.post("/orders/{order_id}/complete", response_model=OrderOut)
def complete_order_endpoint(
    order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    order = _get_owned_order(db, order_id, current_user)
    try:
        return complete_order(db, order)
    except OrderServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_order(db, order_id, current_user)


@router.get("/me/tickets", response_model=list[MyTicketOut])
def list_my_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    registrations = (
        db.query(Registration)
        .filter_by(user_id=current_user.id)
        .order_by(Registration.created_at.desc())
        .all()
    )
    result = []
    for reg in registrations:
        event = db.get(Event, reg.event_id)
        session = db.get(EventSession, reg.session_id)
        result.append(
            MyTicketOut(
                registration=RegistrationOut.model_validate(reg),
                event_title=event.title,
                event_slug=event.slug,
                event_format=event.format.value,
                session_starts_at=session.starts_at,
                session_duration_minutes=session.duration_minutes,
                session_online_join_url=session.online_join_url,
                session_venue_address=session.venue_address or event.venue_address,
            )
        )
    return result


@router.post("/registrations/{registration_id}/cancel", response_model=RegistrationOut)
def cancel_registration_endpoint(
    registration_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ثبت‌نام یافت نشد")
    if registration.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "این ثبت‌نام متعلق به شما نیست")
    try:
        return cancel_registration(db, registration)
    except OrderServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.get("/registrations/{registration_id}/calendar-link")
def get_registration_calendar_link(
    registration_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ثبت‌نام یافت نشد")
    if registration.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "این ثبت‌نام متعلق به شما نیست")

    event = db.get(Event, registration.event_id)
    session = db.get(EventSession, registration.session_id)
    location = event.venue_address or event.online_platform_name or "آنلاین"
    link = google_calendar_link(
        title=event.title,
        description=event.description_plain,
        location=location,
        starts_at=session.starts_at,
        duration_minutes=session.duration_minutes,
    )
    return {"calendar_link": link}
