"""اعتبارسنجی و re-encode امن تصویر — بخش ۱۶ پلن معماری.

آپلود بنر رویداد (و هر آپلود تصویری دیگری) باید از این تابع عبور کند تا
ریسک ویروس/تروجان/payload پنهان‌شده با steganography در یک فایل به‌ظاهر
تصویر سالم خنثی شود. راهبرد: تصویر واقعاً decode می‌شود (نه فقط بررسی
پسوند/Content-Type) و از روی پیکسل‌های واقعی، یک فایل JPEG کاملاً تازه
بدون هیچ متادیتا/بایت اضافی بازتولید می‌شود. فایل ورودی خام هرگز روی
دیسک/MinIO ذخیره نمی‌شود.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # ۵ مگابایت
MAX_DIMENSION_PX = 4000
JPEG_QUALITY = 88

ALLOWED_INPUT_FORMATS = {"JPEG", "PNG", "WEBP"}


class InvalidImageError(ValueError):
    pass


def validate_and_reencode_image(raw: bytes) -> bytes:
    if not raw:
        raise InvalidImageError("فایل خالی است")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise InvalidImageError("حجم فایل نباید بیش از ۵ مگابایت باشد")

    try:
        image = Image.open(io.BytesIO(raw))
        # فرمت واقعی از روی magic bytes خوانده می‌شود، نه پسوند/Content-Type ارسالی کلاینت
        image_format = image.format
    except UnidentifiedImageError as exc:
        raise InvalidImageError("فایل، تصویر معتبری نیست") from exc

    if image_format not in ALLOWED_INPUT_FORMATS:
        raise InvalidImageError("فقط فرمت‌های JPEG، PNG و WebP مجاز است (SVG رد می‌شود)")

    # ابعاد از هدر خوانده می‌شود (بدون decode کامل) تا قبل از پردازش سنگین رد بشه
    if image.width > MAX_DIMENSION_PX or image.height > MAX_DIMENSION_PX:
        raise InvalidImageError("ابعاد تصویر بیش از حد مجاز است")

    try:
        # دیکد کامل پیکسل‌ها؛ Pillow به‌صورت پیش‌فرض در برابر decompression-bomb محافظت می‌کند
        image.load()
    except Exception as exc:
        raise InvalidImageError("فایل تصویر قابل پردازش نیست") from exc

    if image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        clean = Image.new("RGB", rgba.size, (255, 255, 255))
        clean.paste(rgba, mask=rgba.split()[-1])
    else:
        clean = image.convert("RGB")

    output = io.BytesIO()
    clean.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return output.getvalue()
