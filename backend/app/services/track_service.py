"""ثبت رویدادهای رفتاری در Mongo (بخش ۳ و ۱۱ پلن معماری) — فقط لاگ خام،
هیچ‌وقت نباید مسیر اصلی درخواست کاربر رو fail کنه یا کند کنه؛ به همین
دلیل هر خطای اتصال/نوشتن Mongo کاملاً بی‌صدا catch می‌شه (نه راه‌حل دام
#۲۱ با ThreadPoolExecutor، چون insert_one با timeout کوتاه خودش سریع
fail می‌ده، نه اینکه بی‌نهایت آویزون بمونه)."""

from __future__ import annotations

import hashlib
import logging

from pymongo.database import Database

from app.models.base import utcnow

logger = logging.getLogger(__name__)

_COLLECTION_BY_EVENT_TYPE = {
    "page_view": "page_views",
    "search_query": "search_queries",
    "funnel_step": "funnel_events",
    "click": "click_events",
}


def _hash_ip(ip: str | None) -> str | None:
    if not ip or ip == "unknown":
        return None
    return hashlib.sha256(ip.encode()).hexdigest()


def record_event(
    mongo_db: Database,
    event_type: str,
    session_id: str,
    user_id: int | None,
    ip: str | None,
    payload: dict,
) -> None:
    collection_name = _COLLECTION_BY_EVENT_TYPE.get(event_type)
    if collection_name is None:
        return

    document = {
        "session_id": session_id,
        "user_id": user_id,
        "ip_hash": _hash_ip(ip),
        "ts": utcnow(),
        **payload,
    }
    try:
        mongo_db[collection_name].insert_one(document)
    except Exception:
        logger.warning("track event write failed (event_type=%s)", event_type, exc_info=True)
