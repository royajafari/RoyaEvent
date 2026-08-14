"""قالب‌های ثابت اعلان (بخش ۸ پلن معماری) — سه template_key × دو کانال.

پیامک فارسی به‌عمد کوتاهه: پیامک با حروف فارسی با کدگذاری UCS-2 ارسال
می‌شه که هر پارت فقط ۷۰ کاراکتره؛ پیامک طولانی یعنی چند برابر هزینه."""

from __future__ import annotations

from jinja2 import Template

from app.models.notification import NotificationTemplateKey

_SMS_TEMPLATES: dict[NotificationTemplateKey, Template] = {
    NotificationTemplateKey.REGISTRATION_COMPLETE: Template(
        "رویا ایونت: ثبت‌نام شما در «{{ event_title }}» تکمیل شد. "
        "زمان: {{ session_starts_at_jalali }} کد بلیط: {{ ticket_code }}"
    ),
    NotificationTemplateKey.TICKET_PURCHASE_COMPLETE: Template(
        "رویا ایونت: خرید بلیط «{{ ticket_type_name }}» برای «{{ event_title }}» "
        "تکمیل شد. زمان: {{ session_starts_at_jalali }} کد بلیط: {{ ticket_code }}"
    ),
    NotificationTemplateKey.EVENT_REMINDER_1H: Template(
        "رویا ایونت: یادآوری - «{{ event_title }}» یک ساعت دیگر شروع می‌شود "
        "({{ session_starts_at_jalali }})."
    ),
}

_EMAIL_SUBJECT_TEMPLATES: dict[NotificationTemplateKey, Template] = {
    NotificationTemplateKey.REGISTRATION_COMPLETE: Template("ثبت‌نام شما در {{ event_title }} تکمیل شد"),
    NotificationTemplateKey.TICKET_PURCHASE_COMPLETE: Template("خرید بلیط {{ event_title }} تکمیل شد"),
    NotificationTemplateKey.EVENT_REMINDER_1H: Template("یادآوری: {{ event_title }} به‌زودی شروع می‌شود"),
}

_EMAIL_BODY_TEMPLATES: dict[NotificationTemplateKey, Template] = {
    NotificationTemplateKey.REGISTRATION_COMPLETE: Template(
        "<div dir=\"rtl\" style=\"font-family:Tahoma,sans-serif;text-align:right\">"
        "<p>{{ user_name }} عزیز،</p>"
        "<p>ثبت‌نام شما در رویداد <strong>{{ event_title }}</strong> با موفقیت تکمیل شد.</p>"
        "<p>زمان برگزاری: {{ session_starts_at_jalali }}<br>"
        "محل/پلتفرم: {{ location }}<br>"
        "کد بلیط: {{ ticket_code }}</p>"
        "<p><a href=\"{{ calendar_link }}\">افزودن به تقویم گوگل</a></p>"
        "</div>"
    ),
    NotificationTemplateKey.TICKET_PURCHASE_COMPLETE: Template(
        "<div dir=\"rtl\" style=\"font-family:Tahoma,sans-serif;text-align:right\">"
        "<p>{{ user_name }} عزیز،</p>"
        "<p>خرید بلیط <strong>{{ ticket_type_name }}</strong> برای رویداد "
        "<strong>{{ event_title }}</strong> با موفقیت تکمیل شد.</p>"
        "<p>مبلغ پرداختی: {{ ticket_price_formatted }} تومان<br>"
        "زمان برگزاری: {{ session_starts_at_jalali }}<br>"
        "محل/پلتفرم: {{ location }}<br>"
        "کد بلیط: {{ ticket_code }}</p>"
        "<p><a href=\"{{ calendar_link }}\">افزودن به تقویم گوگل</a></p>"
        "</div>"
    ),
    NotificationTemplateKey.EVENT_REMINDER_1H: Template(
        "<div dir=\"rtl\" style=\"font-family:Tahoma,sans-serif;text-align:right\">"
        "<p>{{ user_name }} عزیز،</p>"
        "<p>رویداد <strong>{{ event_title }}</strong> یک ساعت دیگر شروع می‌شود.</p>"
        "<p>زمان برگزاری: {{ session_starts_at_jalali }}<br>"
        "محل/پلتفرم: {{ location }}</p>"
        "</div>"
    ),
}


def render_sms(template_key: NotificationTemplateKey, payload: dict) -> str:
    return _SMS_TEMPLATES[template_key].render(**payload)


def render_email(template_key: NotificationTemplateKey, payload: dict) -> tuple[str, str]:
    subject = _EMAIL_SUBJECT_TEMPLATES[template_key].render(**payload)
    body = _EMAIL_BODY_TEMPLATES[template_key].render(**payload)
    return subject, body
