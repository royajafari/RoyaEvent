"""اعتبارسنجی کلیپ کوتاه تبلیغاتی رویداد (promo_video_url) — کنار بنر، نه جایگزینش.

برخلاف بنر (که re-encode کامل می‌شود، بخش ۱۶ پلن)، ویدیو re-encode واقعی
نیاز به ffmpeg دارد که برای MVP سنگین است؛ به‌جایش فرمت از روی magic bytes
(نه پسوند/Content-Type کلاینت) و سقف حجم سخت‌گیرانه اعتبارسنجی می‌شود و
فایل خام (بدون تغییر) با نام تصادفی در MinIO ذخیره می‌شود — هرگز روی مسیر
قابل‌اجرا سرو نمی‌شود، طبق همون منطق امنیتی بنر.
"""

from __future__ import annotations

MAX_UPLOAD_BYTES = 30 * 1024 * 1024  # ۳۰ مگابایت

_WEBM_MAGIC = b"\x1a\x45\xdf\xa3"


class InvalidVideoError(ValueError):
    pass


def validate_video_file(raw: bytes) -> str:
    """فرمت را از روی magic bytes تشخیص می‌دهد و content_type مناسب را برمی‌گرداند."""
    if not raw:
        raise InvalidVideoError("فایل خالی است")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise InvalidVideoError("حجم کلیپ نباید بیش از ۳۰ مگابایت باشد")

    if raw[:4] == _WEBM_MAGIC:
        return "video/webm"

    # MP4/ISO-BMFF: بایت‌های ۴ تا ۷ باید "ftyp" باشند (بایت‌های ۰-۳ اندازه‌ی باکس‌اند)
    if len(raw) >= 12 and raw[4:8] == b"ftyp":
        return "video/mp4"

    raise InvalidVideoError("فقط فرمت‌های MP4 و WebM مجاز است")
