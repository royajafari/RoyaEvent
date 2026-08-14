from datetime import datetime

from app.core.persian_date import format_jalali_datetime


def test_format_jalali_datetime_converts_utc_to_tehran_and_jalali():
    # ۲۰۲۶-۰۸-۱۳ ۱۰:۳۰ UTC == ۲۲ مرداد ۱۴۰۵ ساعت ۱۴:۰۰ به وقت تهران (+۰۳:۳۰)
    dt = datetime(2026, 8, 13, 10, 30)
    result = format_jalali_datetime(dt)
    assert "1405" in result
    assert "مرداد" in result
    assert "14:00" in result


def test_format_jalali_datetime_crosses_day_boundary_with_tehran_offset():
    # ۲۰۲۶-۰۸-۱۳ ۲۱:۰۰ UTC + ۳:۳۰ = ۲۰۲۶-۰۸-۱۴ ۰۰:۳۰ تهران — روز عوض می‌شود
    dt = datetime(2026, 8, 13, 21, 0)
    result = format_jalali_datetime(dt)
    assert "00:30" in result
