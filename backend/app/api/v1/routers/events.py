import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.core.rate_limit_middleware import limiter
from app.core.storage import upload_banner_image
from app.models.category import Category
from app.models.event import Event, EventStatus, EventVisibility
from app.models.user import User
from app.schemas.event import (
    CategoryOut,
    EventCreateIn,
    EventDetailOut,
    EventListItemOut,
    EventSessionIn,
    EventUpdateIn,
)
from app.services import event_service
from app.services.event_service import EventServiceError
from app.services.image_service import InvalidImageError, validate_and_reencode_image

router = APIRouter(prefix="/events", tags=["events"])

MAX_BANNER_UPLOAD_BYTES = 5 * 1024 * 1024


def _event_query(db: Session):
    return db.query(Event).options(
        selectinload(Event.sessions), selectinload(Event.tags), selectinload(Event.category)
    )


def _to_list_item(event: Event) -> EventListItemOut:
    ordered_sessions = sorted(event.sessions, key=lambda s: s.starts_at)
    next_session = ordered_sessions[0] if ordered_sessions else None
    return EventListItemOut(
        id=event.id,
        title=event.title,
        slug=event.slug,
        event_code=event.event_code,
        banner_url=event.banner_url,
        category=CategoryOut.model_validate(event.category) if event.category else None,
        format=event.format.value,
        status=event.status.value,
        is_featured=event.is_featured,
        rating_avg=event.rating_avg,
        rating_count=event.rating_count,
        view_count=event.view_count,
        next_session_at=next_session.starts_at if next_session else None,
    )


def _require_owner(event: Event, user: User) -> None:
    if event.organizer_id != user.id and user.role.value != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "شما مالک این رویداد نیستید")


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.parent_id.is_(None).desc(), Category.name).all()
    return [CategoryOut.model_validate(c) for c in categories]


@router.get("", response_model=list[EventListItemOut])
def list_events(
    category_id: int | None = None,
    format: str | None = None,
    db: Session = Depends(get_db),
):
    query = _event_query(db).filter(
        Event.status == EventStatus.PUBLISHED, Event.visibility == EventVisibility.PUBLIC
    )
    if category_id is not None:
        query = query.filter(Event.category_id == category_id)
    if format is not None:
        query = query.filter(Event.format == format)

    events = query.order_by(Event.published_at.desc()).limit(50).all()
    return [_to_list_item(e) for e in events]


@router.get("/mine", response_model=list[EventListItemOut])
def list_my_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    events = (
        _event_query(db)
        .filter(Event.organizer_id == current_user.id)
        .order_by(Event.created_at.desc())
        .all()
    )
    return [_to_list_item(e) for e in events]


@router.get("/id/{event_id}", response_model=EventDetailOut)
def get_event_by_id_for_owner(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """برخلاف /{slug}، وضعیت DRAFT هم برمی‌گرداند — فقط برای مالک (پیش‌نمایش/ویرایش)."""
    event = _event_query(db).filter_by(id=event_id).first()
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    _require_owner(event, current_user)
    return event


@router.get("/code/{event_code}", response_model=EventDetailOut)
def get_event_by_code(event_code: str, db: Session = Depends(get_db)):
    event = _event_query(db).filter_by(event_code=event_code).first()
    # پیش‌نویس فقط برای مالک قابل مشاهده است؛ این endpoint عمومی/بدون احراز
    # هویت است پس هرگز نباید رویداد PUBLISHED-نشده رو نشون بده.
    if event is None or event.status != EventStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    if event.visibility == EventVisibility.PRIVATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    return event


@router.get("/private/{token}", response_model=EventDetailOut)
def get_private_event(token: str, db: Session = Depends(get_db)):
    event = _event_query(db).filter_by(private_access_token=token).first()
    if event is None or event.status != EventStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    return event


@router.get("/{slug}", response_model=EventDetailOut)
def get_event_by_slug(slug: str, db: Session = Depends(get_db)):
    event = _event_query(db).filter_by(slug=slug).first()
    # پیش‌نویس (DRAFT) فقط از طریق /events/mine برای مالک قابل مشاهده است؛
    # این endpoint عمومی است، پس رویداد منتشرنشده هرگز نباید نشت کند.
    if event is None or event.status != EventStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    if event.visibility == EventVisibility.PRIVATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    event.view_count += 1
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}/related", response_model=list[EventListItemOut])
def get_related_events(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    query = _event_query(db).filter(
        Event.status == EventStatus.PUBLISHED,
        Event.visibility == EventVisibility.PUBLIC,
        Event.id != event.id,
    )
    if event.category_id is not None:
        query = query.filter(Event.category_id == event.category_id)
    events = query.order_by(Event.rating_avg.desc()).limit(6).all()
    return [_to_list_item(e) for e in events]


@router.post("", response_model=EventDetailOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_event(
    request: Request,
    body: EventCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        event = event_service.create_event(db, current_user.id, body)
    except EventServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    if event.visibility == EventVisibility.PRIVATE:
        event.private_access_token = secrets.token_urlsafe(24)
        db.commit()
        db.refresh(event)

    return event


@router.patch("/{event_id}", response_model=EventDetailOut)
@limiter.limit("20/minute")
def update_event(
    request: Request,
    event_id: int,
    body: EventUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    _require_owner(event, current_user)

    try:
        event = event_service.update_event(db, event, body)
    except EventServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return event


@router.put("/{event_id}/sessions", response_model=EventDetailOut)
@limiter.limit("20/minute")
def replace_event_sessions(
    request: Request,
    event_id: int,
    sessions: list[EventSessionIn],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    _require_owner(event, current_user)

    try:
        event = event_service.replace_sessions(db, event, sessions)
    except EventServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return event


@router.post("/{event_id}/publish", response_model=EventDetailOut)
def publish_event(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    _require_owner(event, current_user)

    try:
        event = event_service.publish_event(db, event)
    except EventServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return event


@router.delete("/{event_id}", response_model=EventDetailOut)
def cancel_event(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    _require_owner(event, current_user)
    return event_service.cancel_event(db, event)


@router.post("/{event_id}/banner", response_model=EventDetailOut)
@limiter.limit("10/minute")
async def upload_event_banner(
    request: Request,
    event_id: int,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    _require_owner(event, current_user)

    raw = await file.read(MAX_BANNER_UPLOAD_BYTES + 1)
    if len(raw) > MAX_BANNER_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "حجم فایل نباید بیش از ۵ مگابایت باشد")

    try:
        clean_jpeg = validate_and_reencode_image(raw)
    except InvalidImageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    banner_url = upload_banner_image(event.id, clean_jpeg)
    return event_service.set_banner_url(db, event, banner_url)
