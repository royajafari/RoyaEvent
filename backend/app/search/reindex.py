"""بازسازی کامل ایندکس ChromaDB از روی رویدادهای PUBLISHED+PUBLIC موجود در
SQLite — لازم برای رویدادهایی که قبل از راه‌اندازی فاز ۴ منتشر شده بودن
(sync_event_index فقط از این به بعد، موقع publish/update/cancel صدا زده
می‌شه) یا اگه پوشه‌ی chroma_data به هر دلیلی پاک/عوض بشه.

اجرا: python -m app.search.reindex
Idempotent است: هر بار کامل از نو upsert می‌کنه، خطایی نداره.
"""

from app.db.session import SessionLocal
from app.models.event import Event, EventStatus, EventVisibility
from app.search.indexer import upsert_event


def reindex_all() -> int:
    db = SessionLocal()
    try:
        events = (
            db.query(Event)
            .filter(Event.status == EventStatus.PUBLISHED, Event.visibility == EventVisibility.PUBLIC)
            .all()
        )
        for event in events:
            upsert_event(event)
        return len(events)
    finally:
        db.close()


if __name__ == "__main__":
    count = reindex_all()
    print(f"{count} رویداد ایندکس شد.")
