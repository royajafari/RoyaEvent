import io
import json
from functools import lru_cache
from uuid import uuid4

from minio import Minio

from app.core.config import get_settings


@lru_cache
def get_minio_client() -> Minio:
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket_ready() -> None:
    """باکت رسانه را در صورت نبود می‌سازد و آن را public-read می‌کند
    (بنر رویداد باید بدون احراز هویت روی صفحه‌ی عمومی رویداد قابل نمایش باشد).
    """
    settings = get_settings()
    client = get_minio_client()
    bucket = settings.minio_bucket
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    client.set_bucket_policy(bucket, json.dumps(policy))


def upload_banner_image(event_id: int, jpeg_bytes: bytes) -> str:
    """آپلود بایت‌های JPEG re-encode‌شده (خروجی validate_and_reencode_image)
    با یک نام تصادفی (نه نام فایل اصلی کاربر) و برگرداندن URL عمومی.
    """
    settings = get_settings()
    client = get_minio_client()
    ensure_bucket_ready()

    object_key = f"banners/{event_id}/{uuid4().hex}.jpg"
    client.put_object(
        settings.minio_bucket,
        object_key,
        data=io.BytesIO(jpeg_bytes),
        length=len(jpeg_bytes),
        content_type="image/jpeg",
    )

    scheme = "https" if settings.minio_secure else "http"
    return f"{scheme}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_key}"


def upload_avatar_image(user_id: int, jpeg_bytes: bytes) -> str:
    """آپلود عکس پروفایل کاربر — دقیقاً همون منطق re-encode امن بنر رویداد،
    فقط با namespace متفاوت در باکت (avatars/{user_id}/...)."""
    settings = get_settings()
    client = get_minio_client()
    ensure_bucket_ready()

    object_key = f"avatars/{user_id}/{uuid4().hex}.jpg"
    client.put_object(
        settings.minio_bucket,
        object_key,
        data=io.BytesIO(jpeg_bytes),
        length=len(jpeg_bytes),
        content_type="image/jpeg",
    )

    scheme = "https" if settings.minio_secure else "http"
    return f"{scheme}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_key}"


def upload_promo_video(event_id: int, raw: bytes, content_type: str) -> str:
    """آپلود کلیپ کوتاه تبلیغاتی رویداد (بدون transcode، طبق تصمیم MVP) با
    نام تصادفی — کنار upload_banner_image، نه جایگزینش.
    """
    settings = get_settings()
    client = get_minio_client()
    ensure_bucket_ready()

    extension = "webm" if content_type == "video/webm" else "mp4"
    object_key = f"promo-videos/{event_id}/{uuid4().hex}.{extension}"
    client.put_object(
        settings.minio_bucket,
        object_key,
        data=io.BytesIO(raw),
        length=len(raw),
        content_type=content_type,
    )

    scheme = "https" if settings.minio_secure else "http"
    return f"{scheme}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_key}"
