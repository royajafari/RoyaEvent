"""اعتبارسنجی شماره موبایل ایرانی و ایمیل — طبق تصمیم بخش ۱۵ پلن معماری:

برای موبایل ایرانی «چک دیجیت» واقعی مثل کدملی وجود ندارد؛ اعتبارسنجی از طریق
فرمت + پیش‌شماره‌های واقعی اپراتور انجام می‌شود. باید همه‌جا که شماره/ایمیل
گرفته می‌شود (ثبت‌نام، خبرنامه، دعوت به رویداد خصوصی و ...) از این توابع
استفاده شود.
"""

import re

# پیش‌شماره‌های فعال اپراتورهای ایرانی (همراه اول، ایرانسل، رایتل و سایر
# اپراتورهای مجازی) — فهرست پرکاربردترین رنج‌های ۰۹xx.
_IRAN_MOBILE_PREFIXES = {
    "901", "902", "903", "904", "905", "930", "933", "935", "936", "937", "938", "939",  # ایرانسل
    "910", "911", "912", "913", "914", "915", "916", "917", "918", "919",  # همراه اول
    "990", "991", "992", "993",  # همراه اول (مجازی)
    "920", "921", "922",  # رایتل
    "999", "998", "997", "996", "994",  # اپراتورهای مجازی/سایر
}

_MOBILE_RE = re.compile(r"^(?:\+98|0098|98|0)?9(\d{2})(\d{7})$")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InvalidPhoneNumber(ValueError):
    pass


class InvalidEmail(ValueError):
    pass


def normalize_iranian_mobile(raw: str) -> str:
    """اعتبارسنجی و نرمال‌سازی شماره موبایل ایرانی به فرمت ۰۹XXXXXXXXX."""
    digits = re.sub(r"[\s\-()]", "", raw or "")
    match = _MOBILE_RE.match(digits)
    if not match:
        raise InvalidPhoneNumber("شماره موبایل نامعتبر است")
    prefix_tail, rest = match.groups()
    operator_prefix = f"9{prefix_tail}"
    if operator_prefix not in _IRAN_MOBILE_PREFIXES:
        raise InvalidPhoneNumber("پیش‌شماره‌ی اپراتور نامعتبر است")
    return f"0{operator_prefix}{rest}"


def validate_email_format(raw: str) -> str:
    email = (raw or "").strip()
    if not _EMAIL_RE.match(email):
        raise InvalidEmail("ایمیل نامعتبر است")
    return email.lower()


def normalize_destination(raw: str, channel: str) -> str:
    if channel == "sms":
        return normalize_iranian_mobile(raw)
    if channel == "email":
        return validate_email_format(raw)
    raise ValueError("کانال نامعتبر است")
