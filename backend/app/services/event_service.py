from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.slug import generate_numeric_code, slugify_ascii
from app.models.base import utcnow
from app.models.category import Category
from app.models.event import Event, EventSession, EventStatus
from app.models.tag import Tag
from app.schemas.event import EventCreateIn, EventSessionIn, EventUpdateIn


class EventServiceError(ValueError):
    pass


def _generate_unique_event_code(db: Session) -> str:
    for _ in range(20):
        code = generate_numeric_code(6)
        if db.query(Event).filter_by(event_code=code).first() is None:
            return code
    raise EventServiceError("امکان تولید کد یکتای رویداد وجود ندارد؛ دوباره تلاش کنید")


def _generate_unique_slug(db: Session, title: str, event_code: str) -> str:
    base = slugify_ascii(title, fallback_prefix="event")
    slug = f"{base}-{event_code}"
    suffix = 1
    while db.query(Event).filter_by(slug=slug).first() is not None:
        suffix += 1
        slug = f"{base}-{event_code}-{suffix}"
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
    )
    event.tags = _get_or_create_tags(db, data.tag_names)

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

    db.commit()
    db.refresh(event)
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
    return event


def cancel_event(db: Session, event: Event) -> Event:
    event.status = EventStatus.CANCELLED
    db.commit()
    db.refresh(event)
    return event


def set_banner_url(db: Session, event: Event, banner_url: str) -> Event:
    event.banner_url = banner_url
    db.commit()
    db.refresh(event)
    return event
