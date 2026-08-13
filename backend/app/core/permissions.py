from fastapi import HTTPException, status

from app.models.event import Event
from app.models.user import User


def require_event_owner(event: Event, user: User) -> None:
    if event.organizer_id != user.id and user.role.value != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "شما مالک این رویداد نیستید")


def require_complete_profile(user: User) -> None:
    """کاربرهای OTP-only معمولاً فقط شماره/ایمیل دارن، نه نام. قبل از اقدامات
    مهم (ایجاد رویداد، خرید بلیط) نام کامل رو اجباری می‌کنیم تا هم برگزارکننده
    با اسم واقعی به شرکت‌کننده‌ها نشون داده بشه، هم بلیط/فاکتور اسم داشته باشه."""
    if not user.full_name or not user.full_name.strip():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "برای این کار باید ابتدا نام و نام خانوادگی خود را تکمیل کنید",
        )
