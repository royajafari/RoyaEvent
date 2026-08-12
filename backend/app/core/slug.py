import re
import secrets
import string


def slugify_ascii(text: str, fallback_prefix: str = "item") -> str:
    """Slug ساده‌ی ASCII از روی بخش‌های لاتین متن؛ اگر متن کاملاً فارسی
    بود (بدون بخش لاتین قابل استفاده)، یک شناسه‌ی تصادفی کوتاه برمی‌گرداند.
    برای رویدادها معمولاً روی این slug، event_code هم اضافه می‌شود تا
    یکتایی تضمین بشه.
    """
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    if not slug:
        random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return f"{fallback_prefix}-{random_suffix}"
    return slug[:150]


def generate_numeric_code(length: int = 6) -> str:
    """کد رویداد عددی (مثل eseminar.tv) — از secrets برای امنیت کافی استفاده می‌شه."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def generate_alnum_code(length: int = 10) -> str:
    """کد بلیط حرفی‌عددی یکتا (ticket_code)."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
