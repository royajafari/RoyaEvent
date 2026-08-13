from datetime import datetime, timedelta

import pytest

from app.models.category import Category
from app.models.event import EventStatus
from app.schemas.event import EventCreateIn, EventSessionIn, EventUpdateIn
from app.services import event_service
from app.services.event_service import EventServiceError


def _future(hours: int) -> datetime:
    return datetime.now() + timedelta(hours=hours)


def _create_in(category_id: int, **overrides) -> EventCreateIn:
    defaults = dict(
        title="کارگاه آموزشی هوش مصنوعی",
        description="توضیحات کامل کارگاه",
        category_id=category_id,
        format="online",
        online_platform_name="SkyRoom",
        visibility="public",
        tag_names=["هوش‌مصنوعی", "ai"],
        sessions=[EventSessionIn(starts_at=_future(48), duration_minutes=90)],
    )
    defaults.update(overrides)
    return EventCreateIn(**defaults)


def test_create_event_generates_unique_code_and_slug(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))

    assert event.event_code.startswith("RE-")
    assert event.event_code[3:].isdigit()
    assert len(event.event_code[3:]) == 6
    assert event.slug.endswith(event.event_code.lower())
    assert event.status == EventStatus.DRAFT
    assert len(event.sessions) == 1
    assert {t.name for t in event.tags} == {"هوش‌مصنوعی", "ai"}


def test_create_event_rejects_parent_category(db_session, leaf_category, organizer):
    parent = db_session.get(Category, leaf_category.parent_id)
    with pytest.raises(EventServiceError):
        event_service.create_event(db_session, organizer.id, _create_in(parent.id))


def test_create_event_sessions_are_ordered_by_start_time(db_session, leaf_category, organizer):
    data = _create_in(
        leaf_category.id,
        sessions=[
            EventSessionIn(starts_at=_future(72), duration_minutes=60),
            EventSessionIn(starts_at=_future(24), duration_minutes=60),
        ],
    )
    event = event_service.create_event(db_session, organizer.id, data)
    assert event.sessions[0].starts_at < event.sessions[1].starts_at
    assert event.sessions[0].sequence_order == 0
    assert event.sessions[1].sequence_order == 1


def test_two_events_get_different_codes(db_session, leaf_category, organizer):
    e1 = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    e2 = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    assert e1.event_code != e2.event_code
    assert e1.slug != e2.slug


def test_reusing_same_tag_name_does_not_duplicate_tag_rows(db_session, leaf_category, organizer):
    event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))

    from app.models.tag import Tag

    assert db_session.query(Tag).filter_by(name="ai").count() == 1


def test_publish_requires_at_least_one_session(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    event.sessions.clear()
    db_session.commit()

    with pytest.raises(EventServiceError):
        event_service.publish_event(db_session, event)


def test_publish_sets_status_and_timestamp(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    published = event_service.publish_event(db_session, event)
    assert published.status == EventStatus.PUBLISHED
    assert published.published_at is not None


def test_publish_twice_fails(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    event_service.publish_event(db_session, event)
    with pytest.raises(EventServiceError):
        event_service.publish_event(db_session, event)


def test_cancel_sets_status(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    cancelled = event_service.cancel_event(db_session, event)
    assert cancelled.status == EventStatus.CANCELLED


def test_update_event_title_and_tags(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    updated = event_service.update_event(
        db_session, event, EventUpdateIn(title="عنوان جدید", tag_names=["تگ‌جدید"])
    )
    assert updated.title == "عنوان جدید"
    assert {t.name for t in updated.tags} == {"تگ‌جدید"}


def test_replace_sessions_rejects_empty_list(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    with pytest.raises(EventServiceError):
        event_service.replace_sessions(db_session, event, [])


def test_replace_sessions_replaces_all(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    new_sessions = [
        EventSessionIn(starts_at=_future(10), duration_minutes=30),
        EventSessionIn(starts_at=_future(20), duration_minutes=45),
    ]
    updated = event_service.replace_sessions(db_session, event, new_sessions)
    assert len(updated.sessions) == 2


def test_set_banner_url(db_session, leaf_category, organizer):
    event = event_service.create_event(db_session, organizer.id, _create_in(leaf_category.id))
    updated = event_service.set_banner_url(db_session, event, "http://minio.local/bucket/x.jpg")
    assert updated.banner_url == "http://minio.local/bucket/x.jpg"
