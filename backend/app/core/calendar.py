"""تولید لینک «افزودن به Google Calendar» — بدون OAuth/API call/ذخیره‌سازی
(تصمیم صریح کاربر، بخش ۸ پلن معماری)."""

from datetime import datetime, timedelta
from urllib.parse import urlencode

_DATE_FORMAT = "%Y%m%dT%H%M%SZ"


def google_calendar_link(
    *, title: str, description: str, location: str, starts_at: datetime, duration_minutes: int
) -> str:
    ends_at = starts_at + timedelta(minutes=duration_minutes)
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{starts_at.strftime(_DATE_FORMAT)}/{ends_at.strftime(_DATE_FORMAT)}",
        "details": description,
        "location": location,
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)
