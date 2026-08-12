from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.ticket import DiscountCode, DiscountType, PlatformDiscountCode

DiscountRecord = DiscountCode | PlatformDiscountCode


def _is_usable(record: DiscountRecord) -> bool:
    now = utcnow()
    if not record.is_active:
        return False
    if record.valid_from and now < record.valid_from:
        return False
    if record.valid_until and now > record.valid_until:
        return False
    if record.max_uses is not None and record.uses_count >= record.max_uses:
        return False
    return True


def find_valid_discount(db: Session, event_id: int, code: str) -> DiscountRecord | None:
    """اول سطح رویداد، بعد سطح سایت (ادمین) — طبق تصمیم کاربر هر دو سطح چک می‌شن."""
    event_code = db.query(DiscountCode).filter_by(event_id=event_id, code=code).first()
    if event_code is not None and _is_usable(event_code):
        return event_code

    platform_code = db.query(PlatformDiscountCode).filter_by(code=code).first()
    if platform_code is not None and _is_usable(platform_code):
        return platform_code

    return None


def compute_discount_amount(subtotal: int, record: DiscountRecord) -> int:
    if record.discount_type == DiscountType.PERCENT:
        amount = round(subtotal * record.value / 100)
    else:
        amount = round(record.value)
    return max(0, min(amount, subtotal))
