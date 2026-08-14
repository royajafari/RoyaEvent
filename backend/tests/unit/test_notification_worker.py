from datetime import timedelta

from app.core.config import get_settings
from app.models.base import utcnow
from app.models.event import EventStatus
from app.models.notification import (
    NotificationChannel,
    NotificationOutbox,
    NotificationStatus,
    NotificationTemplateKey,
)
from app.models.order import Registration
from app.providers.email.base import EmailSendResult
from app.providers.sms.base import SmsSendResult
from app.schemas.order import OrderCreateIn
from app.services.order_service import complete_order, create_order
from app.workers import scheduler


class _FakeSmsProvider:
    def __init__(self, success: bool = True):
        self.success = success
        self.sent: list[tuple[str, str]] = []

    def send(self, destination, message):
        self.sent.append((destination, message))
        return SmsSendResult(provider="fake-sms", provider_message_id="msg-1", success=self.success)


class _FakeEmailProvider:
    def __init__(self, success: bool = True):
        self.success = success
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to_email, subject, html_content):
        self.sent.append((to_email, subject, html_content))
        return EmailSendResult(provider="fake-email", provider_message_id="msg-2", success=self.success)


def _pending_row(db_session, buyer, *, channel=NotificationChannel.SMS, attempts=0, next_attempt_at=None):
    row = NotificationOutbox(
        user_id=buyer.id,
        event_id=None,
        channel=channel,
        destination=buyer.phone if channel == NotificationChannel.SMS else "buyer@example.com",
        template_key=NotificationTemplateKey.EVENT_REMINDER_1H,
        payload_json=(
            '{"event_title": "کارگاه تست", "session_starts_at_jalali": "22 مرداد", "location": "SkyRoom"}'
        ),
        attempts=attempts,
        next_attempt_at=next_attempt_at or utcnow(),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def test_dispatch_outbox_sends_sms_and_marks_sent(db_session, buyer, monkeypatch):
    fake = _FakeSmsProvider(success=True)
    monkeypatch.setattr(scheduler, "get_sms_provider", lambda: fake)
    row = _pending_row(db_session, buyer)

    scheduler.dispatch_outbox(db=db_session)

    db_session.refresh(row)
    assert row.status == NotificationStatus.SENT
    assert row.provider == "fake-sms"
    assert row.attempts == 1
    assert len(fake.sent) == 1
    assert "کارگاه تست" in fake.sent[0][1]


def test_dispatch_outbox_sends_email_and_marks_sent(db_session, buyer, monkeypatch):
    fake = _FakeEmailProvider(success=True)
    monkeypatch.setattr(scheduler, "get_email_provider", lambda: fake)
    row = _pending_row(db_session, buyer, channel=NotificationChannel.EMAIL)

    scheduler.dispatch_outbox(db=db_session)

    db_session.refresh(row)
    assert row.status == NotificationStatus.SENT
    assert len(fake.sent) == 1


def test_dispatch_outbox_retries_with_backoff_on_failure(db_session, buyer, monkeypatch):
    fake = _FakeSmsProvider(success=False)
    monkeypatch.setattr(scheduler, "get_sms_provider", lambda: fake)
    row = _pending_row(db_session, buyer)

    scheduler.dispatch_outbox(db=db_session)

    db_session.refresh(row)
    assert row.status == NotificationStatus.PENDING
    assert row.attempts == 1
    assert row.next_attempt_at > utcnow()
    assert row.last_error


def test_dispatch_outbox_marks_failed_after_max_attempts(db_session, buyer, monkeypatch):
    fake = _FakeSmsProvider(success=False)
    monkeypatch.setattr(scheduler, "get_sms_provider", lambda: fake)
    max_attempts = get_settings().notification_max_attempts
    row = _pending_row(db_session, buyer, attempts=max_attempts - 1)

    scheduler.dispatch_outbox(db=db_session)

    db_session.refresh(row)
    assert row.status == NotificationStatus.FAILED


def test_dispatch_outbox_ignores_rows_not_yet_due(db_session, buyer, monkeypatch):
    fake = _FakeSmsProvider(success=True)
    monkeypatch.setattr(scheduler, "get_sms_provider", lambda: fake)
    row = _pending_row(db_session, buyer, next_attempt_at=utcnow() + timedelta(minutes=10))

    scheduler.dispatch_outbox(db=db_session)

    db_session.refresh(row)
    assert row.status == NotificationStatus.PENDING
    assert row.attempts == 0
    assert len(fake.sent) == 0


def _registration_at(db_session, published_event, buyer, free_ticket_type, *, minutes_from_now):
    session = published_event.sessions[0]
    order = create_order(
        db_session, buyer.id, OrderCreateIn(ticket_type_id=free_ticket_type.id, session_id=session.id)
    )
    complete_order(db_session, order)
    registration = db_session.query(Registration).filter_by(user_id=buyer.id).one()

    session.starts_at = utcnow() + timedelta(minutes=minutes_from_now)
    db_session.commit()
    db_session.refresh(registration)
    return registration


def test_scan_reminders_enqueues_within_window_and_marks_sent_at(
    db_session, published_event, buyer, free_ticket_type
):
    registration = _registration_at(db_session, published_event, buyer, free_ticket_type, minutes_from_now=60)

    scheduler.scan_reminders(db=db_session)

    db_session.refresh(registration)
    assert registration.reminder_sent_at is not None
    rows = db_session.query(NotificationOutbox).filter_by(
        user_id=buyer.id, template_key=NotificationTemplateKey.EVENT_REMINDER_1H
    ).all()
    assert len(rows) == 1


def test_scan_reminders_skips_outside_window(db_session, published_event, buyer, free_ticket_type):
    registration = _registration_at(
        db_session, published_event, buyer, free_ticket_type, minutes_from_now=180
    )

    scheduler.scan_reminders(db=db_session)

    db_session.refresh(registration)
    assert registration.reminder_sent_at is None


def test_scan_reminders_skips_already_reminded(db_session, published_event, buyer, free_ticket_type):
    registration = _registration_at(db_session, published_event, buyer, free_ticket_type, minutes_from_now=60)
    registration.reminder_sent_at = utcnow()
    db_session.commit()

    scheduler.scan_reminders(db=db_session)

    rows = db_session.query(NotificationOutbox).filter_by(
        user_id=buyer.id, template_key=NotificationTemplateKey.EVENT_REMINDER_1H
    ).all()
    assert len(rows) == 0


def test_scan_reminders_skips_unpublished_event(db_session, published_event, buyer, free_ticket_type):
    registration = _registration_at(db_session, published_event, buyer, free_ticket_type, minutes_from_now=60)
    published_event.status = EventStatus.CANCELLED
    db_session.commit()

    scheduler.scan_reminders(db=db_session)

    db_session.refresh(registration)
    assert registration.reminder_sent_at is None
