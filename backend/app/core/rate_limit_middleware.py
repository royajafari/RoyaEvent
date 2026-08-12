"""میان‌افزار rate-limit عمومی — بخش ۶ پلن معماری.

جدا از محدودیت‌های اختصاصی OTP (app/core/rate_limit.py) که خودشان روی
Redis پیاده‌سازی شده‌اند. اینجا از slowapi برای محافظت عمومی کل API
استفاده می‌شود؛ endpointهای OTP با limiter.exempt از این لایه مستثنا
هستند تا دوبار محدود نشوند.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import decode_token


def rate_limit_key(request: Request) -> str:
    """اگر کاربر احرازشده باشد بر اساس user_id، وگرنه بر اساس IP محدود می‌شود."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
        try:
            payload = decode_token(token)
            if payload.get("type") == "access":
                return f"user:{payload['sub']}"
        except ValueError:
            pass
    return f"ip:{get_remote_address(request)}"


# سقف عمومی پیش‌فرض؛ endpointهای پرهزینه (ایجاد رویداد، سفارش و ...) با
# دکوریتور @limiter.limit روی خودشان سخت‌گیرانه‌تر می‌شوند.
limiter = Limiter(key_func=rate_limit_key, default_limits=["120/minute"])
