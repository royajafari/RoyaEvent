from app.models.notification import NotificationTemplateKey
from app.services.notification_templates import render_email, render_sms

_PAYLOAD = {
    "user_name": "علی رضایی",
    "event_title": "کارگاه هوش مصنوعی",
    "session_starts_at_jalali": "22 مرداد 1405 ساعت 14:00",
    "location": "SkyRoom",
    "ticket_code": "ABCDEFGHIJ",
    "calendar_link": "https://calendar.google.com/calendar/render?...",
    "ticket_type_name": "بلیط ویژه",
    "ticket_price_formatted": "150,000",
}


def test_render_sms_all_templates():
    for key in NotificationTemplateKey:
        text = render_sms(key, _PAYLOAD)
        assert "کارگاه هوش مصنوعی" in text
        assert "رویا ایونت" in text


def test_render_email_all_templates():
    for key in NotificationTemplateKey:
        subject, body = render_email(key, _PAYLOAD)
        assert "کارگاه هوش مصنوعی" in subject
        assert "علی رضایی" in body
        assert "کارگاه هوش مصنوعی" in body


def test_render_sms_registration_complete_contains_ticket_code():
    text = render_sms(NotificationTemplateKey.REGISTRATION_COMPLETE, _PAYLOAD)
    assert "ABCDEFGHIJ" in text


def test_render_email_purchase_complete_contains_price():
    _, body = render_email(NotificationTemplateKey.TICKET_PURCHASE_COMPLETE, _PAYLOAD)
    assert "150,000" in body
