"""کلاینت ChromaDB embedded — بخش ۲ پلن معماری (تصمیم کاربر: ChromaDB نه
Qdrant). یک پردازه‌ی جدا/سرویس اضافه نیست؛ کتابخانه‌ای که مستقیم داخل
پردازه‌ی FastAPI با یک پوشه‌ی محلی (chroma_persist_dir) کار می‌کنه.
"""

from functools import lru_cache

import chromadb

from app.core.config import get_settings

EVENTS_COLLECTION = "events"


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_events_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(EVENTS_COLLECTION)
