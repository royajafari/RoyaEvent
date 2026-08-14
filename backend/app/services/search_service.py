"""جستجوی دوگانه — بخش ۹ پلن معماری: قبل از جستجوی وکتور، تطبیق سبک
prefix روی نام برگزارکننده‌ها/مدرس‌ها اجرا می‌شه (بخش «افراد»)، مستقل از
نتایج رویداد. SQLite همیشه منبع حقیقت نهایی برای فیلدهای قابل فیلتر
می‌مونه — ChromaDB فقط شباهت معنایی/ترتیب رو می‌ده، ایدها رو از SQLite
با فیلتر وضعیت/دسته/فرمت می‌گیریم.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus, EventVisibility
from app.models.instructor import Instructor
from app.models.user import User
from app.schemas.search import PersonResultOut
from app.search.chroma_client import get_events_collection
from app.search.embeddings import embed_text
from app.services.event_service import event_query, to_list_item_out

PEOPLE_LIMIT = 5
EVENTS_LIMIT = 30


def search_people(db: Session, query: str) -> list[PersonResultOut]:
    pattern = f"{query.strip()}%"
    if not query.strip():
        return []

    instructors = db.query(Instructor).filter(Instructor.name.ilike(pattern)).limit(PEOPLE_LIMIT).all()

    organizer_ids = [
        row[0]
        for row in db.query(Event.organizer_id)
        .filter(Event.status == EventStatus.PUBLISHED, Event.visibility == EventVisibility.PUBLIC)
        .distinct()
        .all()
    ]
    organizers = (
        db.query(User)
        .filter(User.id.in_(organizer_ids), User.full_name.ilike(pattern))
        .limit(PEOPLE_LIMIT)
        .all()
        if organizer_ids
        else []
    )

    results = [
        PersonResultOut(type="instructor", id=i.id, name=i.name, avatar_url=i.avatar_url)
        for i in instructors
    ] + [
        PersonResultOut(type="organizer", id=u.id, name=u.full_name or "", avatar_url=u.avatar_url)
        for u in organizers
    ]
    return results[:PEOPLE_LIMIT]


def search_events(
    db: Session,
    query: str,
    *,
    category_id: int | None = None,
    format: str | None = None,
):
    collection = get_events_collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[embed_text(query)],
        n_results=min(EVENTS_LIMIT, collection.count()),
    )
    ids = [int(raw_id) for raw_id in result["ids"][0]] if result["ids"] else []
    if not ids:
        return []

    events_query = event_query(db).filter(
        Event.id.in_(ids),
        Event.status == EventStatus.PUBLISHED,
        Event.visibility == EventVisibility.PUBLIC,
    )
    if category_id is not None:
        events_query = events_query.filter(Event.category_id == category_id)
    if format is not None:
        events_query = events_query.filter(Event.format == format)

    events = events_query.all()
    # ترتیب شباهت وکتور (ids همون ترتیبه) رو حفظ کن؛ filter(in_) خودش
    # مرتب‌سازی نمی‌ده
    rank = {event_id: index for index, event_id in enumerate(ids)}
    events.sort(key=lambda e: rank.get(e.id, len(ids)))

    return [to_list_item_out(e) for e in events]


def suggest(db: Session, query: str, limit: int = 8) -> list[str]:
    """پیشنهاد سریع بدون embedding (برای autocomplete موقع تایپ) — فقط
    LIKE ساده روی عنوان رویداد، نه جستجوی معنایی."""
    pattern = f"%{query.strip()}%"
    if not query.strip():
        return []
    titles = (
        db.query(Event.title)
        .filter(
            Event.status == EventStatus.PUBLISHED,
            Event.visibility == EventVisibility.PUBLIC,
            Event.title.ilike(pattern),
        )
        .limit(limit)
        .all()
    )
    return [row[0] for row in titles]
