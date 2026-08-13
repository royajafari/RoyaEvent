"""ایندکس/حذف embedding رویداد در ChromaDB — فقط رویدادهای PUBLISHED+PUBLIC
قابل جستجو هستن (طبق قاعده‌ی دائمی CLAUDE.md: وضعیت DRAFT/CANCELLED/PRIVATE
هرگز نباید از مسیر عمومی — از جمله جستجو — قابل دیدن باشه).
"""

from __future__ import annotations

from app.models.event import Event, EventStatus, EventVisibility
from app.search.chroma_client import get_events_collection
from app.search.embeddings import embed_text


def _document_text(event: Event) -> str:
    return f"{event.title}\n{event.description_plain}"


def sync_event_index(event: Event) -> None:
    """بعد از هر تغییری که ممکنه وضعیت جستجوپذیری/محتوای رویداد رو عوض کنه
    (publish، ویرایش عنوان/توضیحات، لغو) صدا زده می‌شه؛ خودش تصمیم می‌گیره
    upsert کنه یا از ایندکس حذف کنه."""
    is_searchable = event.status == EventStatus.PUBLISHED and event.visibility == EventVisibility.PUBLIC
    if is_searchable:
        upsert_event(event)
    else:
        remove_event(event.id)


def upsert_event(event: Event) -> None:
    collection = get_events_collection()
    collection.upsert(
        ids=[str(event.id)],
        embeddings=[embed_text(_document_text(event))],
        metadatas=[
            {
                "category_id": event.category_id or 0,
                "format": event.format.value,
            }
        ],
        documents=[_document_text(event)],
    )


def remove_event(event_id: int) -> None:
    collection = get_events_collection()
    collection.delete(ids=[str(event_id)])
