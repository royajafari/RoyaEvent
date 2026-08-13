"""مدل embedding چندزبانه برای جستجوی معنایی — بخش ۲ پلن معماری.

paraphrase-multilingual-MiniLM-L12-v2: پشتیبانی فارسی، سبک و CPU-friendly
(بدون نیاز به GPU/API خارجی). مدل فقط بار اولی که واقعاً لازم بشه از
HuggingFace Hub دانلود و کش می‌شه (~۴۷۰ مگابایت)، نه موقع import ماژول —
تا import شدن این فایل (مثلاً در تست‌هایی که کاری با جستجو ندارن) گیر
دانلود شبکه نیفته.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()
