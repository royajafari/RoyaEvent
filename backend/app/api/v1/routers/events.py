import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import require_complete_profile, require_event_owner
from app.core.rate_limit_middleware import limiter
from app.core.storage import upload_banner_image, upload_promo_video
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
from app.services.event_service import EventServiceError, event_query, to_list_item_out
from app.services.image_service import InvalidImageError, validate_and_reencode_image
from app.services.video_service import InvalidVideoError, validate_video_file

router = APIRouter(prefix="/events", tags=["events"])

MAX_BANNER_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PROMO_VIDEO_UPLOAD_BYTES = 30 * 1024 * 1024

_event_query = event_query
_to_list_item = to_list_item_out


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.parent_id.is_(None).desc(), Category.name).all()
    return [CategoryOut.model_validate(c) for c in categories]


@router.get("", response_model=list[EventListItemOut])
def list_events(
    category_id: int | None = None,
    format: str | None = None,
    sort: str | None = None,
    featured: bool | None = None,
    db: Session = Depends(get_db),
):
    query = _event_query(db).filter(
        Event.status == EventStatus.PUBLISHED, Event.visibility == EventVisibility.PUBLIC
    )
    if category_id is not None:
        query = query.filter(Event.category_id == category_id)
    if format is not None:
        query = query.filter(Event.format == format)
    if featured is not None:
        query = query.filter(Event.is_featured == featured)

    # sort=popular: بازدید تنها معیار محبوبیت واقعیه که الان داریم — سیستم
    # امتیازدهی هنوز پیاده نشده (فاز ۷)، پس rating_avg برای همه صفره
    if sort == "popular":
        query = query.order_by(Event.view_count.desc())
    else:
        query = query.order_by(Event.published_at.desc())

    events = query.limit(50).all()
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
    require_event_owner(event, current_user)
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
    require_complete_profile(current_user)
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
    require_event_owner(event, current_user)

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
    require_event_owner(event, current_user)

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
    require_event_owner(event, current_user)

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
    require_event_owner(event, current_user)
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
    require_event_owner(event, current_user)

    raw = await file.read(MAX_BANNER_UPLOAD_BYTES + 1)
    if len(raw) > MAX_BANNER_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "حجم فایل نباید بیش از ۵ مگابایت باشد")

    try:
        clean_jpeg = validate_and_reencode_image(raw)
    except InvalidImageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    banner_url = upload_banner_image(event.id, clean_jpeg)
    return event_service.set_banner_url(db, event, banner_url)


@router.post("/{event_id}/promo-video", response_model=EventDetailOut)
@limiter.limit("10/minute")
async def upload_event_promo_video(
    request: Request,
    event_id: int,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    require_event_owner(event, current_user)

    raw = await file.read(MAX_PROMO_VIDEO_UPLOAD_BYTES + 1)
    if len(raw) > MAX_PROMO_VIDEO_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "حجم کلیپ نباید بیش از ۳۰ مگابایت باشد")

    try:
        content_type = validate_video_file(raw)
    except InvalidVideoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    promo_video_url = upload_promo_video(event.id, raw, content_type)
    return event_service.set_promo_video_url(db, event, promo_video_url)
