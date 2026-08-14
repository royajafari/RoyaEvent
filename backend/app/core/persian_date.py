"""تبدیل UTC به تاریخ/ساعت شمسی تهران — برای متن پیامک/ایمیل (فاز ۶).

برخلاف lib/date.ts فرانت (که نمایش شمسی رو با Intl بومی مرورگر کاربر انجام
می‌ده)، اینجا سرور مستقیم به کاربر پیامک/ایمیل می‌فرسته، مرورگری در کار
نیست که timezone/calendar رو خودش تبدیل کنه — پس این تبدیل باید صریح روی
سرور انجام بشه.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import jdatetime

_UTC = ZoneInfo("UTC")
_TEHRAN = ZoneInfo("Asia/Tehran")


def format_jalali_datetime(dt: datetime) -> str:
    """dt باید naive UTC باشه (قرارداد همیشگی پروژه، app.models.base.utcnow)."""
    aware_utc = dt.replace(tzinfo=_UTC)
    tehran = aware_utc.astimezone(_TEHRAN)
    jdt = jdatetime.datetime.fromgregorian(datetime=tehran)
    return jdt.strftime("%d %B %Y ساعت %H:%M")
