from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from sqlalchemy.orm import Session, selectinload

from app.core.slug import generate_event_code, slugify_ascii
from app.models.base import utcnow
from app.models.category import Category
from app.models.event import Event, EventSession, EventStatus
from app.models.instructor import Instructor
from app.models.tag import Tag
from app.schemas.event import CategoryOut, EventCreateIn, EventListItemOut, EventSessionIn, EventUpdateIn
from app.search.indexer import sync_event_index

logger = logging.getLogger(__name__)

# ایندکس جستجو یه بهبود جانبیه، نه بخشی از تراکنش اصلی. اجراش تو یه thread
# جدا با timeout کوتاه انجام می‌شه چون فقط «try/except دور خطا» کافی نیست —
# روی شبکه‌ی ناپایدار این محیط، دانلود مدل embedding (بار اول که هنوز کش
# نشده) می‌تونه داده رو خیلی کند trickle کنه بدون قطعی کامل، پس هیچ‌وقت
# استثنا/timeout سطح‌شبکه رو تریگر نمی‌کنه و درخواست publish/update رویداد
# رو دقیقه‌ها معطل نگه می‌داره. با اجرا تو thread جدا، اگه ظرف چند ثانیه
# تموم نشد، درخواست اصلی ادامه می‌ده (thread پس‌زمینه هرچقدر لازمه صبر
# می‌کنه، بی‌ضرره چون فقط property های اسکالر از قبل لود‌شده‌ی event رو
# می‌خونه، نه رابطه‌ای که نیاز به session زنده داشته باشه).
_INDEX_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="search-index")
_INDEX_TIMEOUT_SECONDS = 3


def _safe_sync_event_index(event: Event) -> None:
    future = _INDEX_EXECUTOR.submit(sync_event_index, event)
    try:
        future.result(timeout=_INDEX_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        logger.warning("sync_event_index timed out for event %s (continuing in background)", event.id)
    except Exception:
        logger.warning("sync_event_index failed for event %s", event.id, exc_info=True)


class EventServiceError(ValueError):
    pass


def event_query(db: Session):
    return db.query(Event).filter(Event.deleted_at.is_(None)).options(
        selectinload(Event.sessions),
        selectinload(Event.tags),
        selectinload(Event.instructors),
        selectinload(Event.category),
        selectinload(Event.organizer),
    )


def to_list_item_out(event: Event) -> EventListItemOut:
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
        is_instant_registration=event.is_instant_registration,
        rating_avg=event.rating_avg,
        rating_count=event.rating_count,
        view_count=event.view_count,
        next_session_at=next_session.starts_at if next_session else None,
    )


def _generate_unique_event_code(db: Session) -> str:
    for _ in range(20):
        code = generate_event_code(6)
        if db.query(Event).filter_by(event_code=code).first() is None:
            return code
    raise EventServiceError("امکان تولید کد یکتای رویداد وجود ندارد؛ دوباره تلاش کنید")


def _generate_unique_slug(db: Session, title: str, event_code: str) -> str:
    base = slugify_ascii(title, fallback_prefix="event")
    code_slug = event_code.lower()
    slug = f"{base}-{code_slug}"
    suffix = 1
    while db.query(Event).filter_by(slug=slug).first() is not None:
        suffix += 1
        slug = f"{base}-{code_slug}-{suffix}"
    return slug


def _validate_leaf_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise EventServiceError("دسته‌بندی یافت نشد")
    if category.parent_id is None:
        raise EventServiceError("باید یک زیردسته (نه دسته‌ی والد) انتخاب شود")
    return category


def _get_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for raw_name in tag_names:
        name = raw_name.strip().lstrip("#")
        if not name:
            continue
        tag = db.query(Tag).filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name, slug=slugify_ascii(name, fallback_prefix="tag"))
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def _get_or_create_instructors(db: Session, instructor_names: list[str]) -> list[Instructor]:
    """مثل _get_or_create_tags: برگزارکننده فقط اسم مدرس رو تایپ می‌کنه؛ اولین
    بار رکورد Instructor ساخته می‌شه، دفعات بعد همون رکورد پیدا و لینک می‌شه."""
    instructors: list[Instructor] = []
    for raw_name in instructor_names:
        name = raw_name.strip()
        if not name:
            continue
        instructor = db.query(Instructor).filter_by(name=name).first()
        if instructor is None:
            instructor = Instructor(name=name)
            db.add(instructor)
            db.flush()
        instructors.append(instructor)
    return instructors


def create_event(db: Session, organizer_id: int, data: EventCreateIn) -> Event:
    _validate_leaf_category(db, data.category_id)

    event_code = _generate_unique_event_code(db)
    slug = _generate_unique_slug(db, data.title, event_code)

    event = Event(
        organizer_id=organizer_id,
        title=data.title,
        slug=slug,
        event_code=event_code,
        description=data.description,
        description_plain=data.description,
        category_id=data.category_id,
        visibility=data.visibility,
        format=data.format,
        venue_address=data.venue_address,
        online_platform_name=data.online_platform_name,
        refund_policy=data.refund_policy,
        status=EventStatus.DRAFT,
        is_instant_registration=data.is_instant_registration,
    )
    event.tags = _get_or_create_tags(db, data.tag_names)
    event.instructors = _get_or_create_instructors(db, data.instructor_names)

    for index, session_in in enumerate(
        sorted(data.sessions, key=lambda s: s.starts_at)
    ):
        event.sessions.append(_build_session(session_in, index))

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _build_session(session_in: EventSessionIn, sequence_order: int) -> EventSession:
    return EventSession(
        starts_at=session_in.starts_at,
        duration_minutes=session_in.duration_minutes,
        sequence_order=sequence_order,
        venue_address=session_in.venue_address,
        online_join_url=session_in.online_join_url,
        capacity=session_in.capacity,
    )


def update_event(db: Session, event: Event, data: EventUpdateIn) -> Event:
    if data.category_id is not None:
        _validate_leaf_category(db, data.category_id)
        event.category_id = data.category_id
    if data.title is not None:
        event.title = data.title
    if data.description is not None:
        event.description = data.description
        event.description_plain = data.description
    if data.format is not None:
        event.format = data.format
    if data.venue_address is not None:
        event.venue_address = data.venue_address
    if data.online_platform_name is not None:
        event.online_platform_name = data.online_platform_name
    if data.refund_policy is not None:
        event.refund_policy = data.refund_policy
    if data.tag_names is not None:
        event.tags = _get_or_create_tags(db, data.tag_names)
    if data.instructor_names is not None:
        event.instructors = _get_or_create_instructors(db, data.instructor_names)
    if data.is_instant_registration is not None:
        event.is_instant_registration = data.is_instant_registration

    db.commit()
    db.refresh(event)
    if event.status == EventStatus.PUBLISHED:
        _safe_sync_event_index(event)
    return event


def replace_sessions(db: Session, event: Event, sessions_in: list[EventSessionIn]) -> Event:
    if not sessions_in:
        raise EventServiceError("هر رویداد باید حداقل یک جلسه داشته باشد")
    event.sessions.clear()
    db.flush()
    for index, session_in in enumerate(sorted(sessions_in, key=lambda s: s.starts_at)):
        event.sessions.append(_build_session(session_in, index))
    db.commit()
    db.refresh(event)
    return event


def publish_event(db: Session, event: Event) -> Event:
    if event.status != EventStatus.DRAFT:
        raise EventServiceError("فقط رویداد پیش‌نویس قابل انتشار است")
    if not event.sessions:
        raise EventServiceError("رویداد بدون جلسه قابل انتشار نیست")
    event.status = EventStatus.PUBLISHED
    event.published_at = utcnow()
    db.commit()
    db.refresh(event)
    _safe_sync_event_index(event)
    return event


def cancel_event(db: Session, event: Event) -> Event:
    event.status = EventStatus.CANCELLED
    db.commit()
    db.refresh(event)
    _safe_sync_event_index(event)
    return event


def set_banner_url(db: Session, event: Event, banner_url: str) -> Event:
    event.banner_url = banner_url
    db.commit()
    db.refresh(event)
    return event


def set_promo_video_url(db: Session, event: Event, promo_video_url: str) -> Event:
    event.promo_video_url = promo_video_url
    db.commit()
    db.refresh(event)
    return event
