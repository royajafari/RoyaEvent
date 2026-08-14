"""مدل embedding چندزبانه برای جستجوی معنایی — بخش ۲ پلن معماری.

paraphrase-multilingual-MiniLM-L12-v2: پشتیبانی فارسی، سبک و CPU-friendly
(بدون نیاز به GPU/API خارجی). مدل فقط بار اولی که واقعاً لازم بشه از
HuggingFace Hub دانلود و کش می‌شه (~۴۷۰ مگابایت)، نه موقع import ماژول —
تا import شدن این فایل (مثلاً در تست‌هایی که کاری با جستجو ندارن) گیر
دانلود شبکه نیفته.

نکته‌ی مهم: `HF_HUB_DOWNLOAD_TIMEOUT` رو کوتاه (۵ ثانیه) ست می‌کنیم — روی
شبکه‌ی ناپایدار این محیط، دانلود مدل گاهی به‌جای خطای سریع، چند دقیقه
داده‌ی خیلی کند trickle می‌کرد (نه قطع کامل، پس timeout پیش‌فرض/بلند رد
نمی‌شد) و درخواست publish/update رویداد (که event_service.py صداش می‌زنه)
رو همون‌قدر معطل نگه می‌داشت. با این timeout کوتاه، شکست سریع اتفاق
می‌افته و event_service._safe_sync_event_index می‌تونه واقعاً «best effort»
باشه، نه یه بلاک‌کننده‌ی پنهون.
"""

import os
from functools import lru_cache

os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "5")

from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()
