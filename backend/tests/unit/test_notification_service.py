import json

from app.models.notification import NotificationChannel, NotificationOutbox, NotificationTemplateKey
from app.models.order import Registration
from app.schemas.order import OrderCreateIn
from app.services import notification_service
from app.services.order_service import complete_order, create_order


def test_enqueue_creates_row_per_available_channel(db_session, organizer):
    organizer.email = "organizer@example.com"
    db_session.commit()

    rows = notification_service.enqueue(
        db_session,
        user=organizer,
        event_id=None,
        template_key=NotificationTemplateKey.EVENT_REMINDER_1H,
        payload={"event_title": "تست"},
    )

    assert {r.channel for r in rows} == {NotificationChannel.SMS, NotificationChannel.EMAIL}
    assert all(r.status.value == "pending" for r in rows)
    saved = db_session.query(NotificationOutbox).all()
    assert len(saved) == 2


def test_enqueue_skips_missing_channels(db_session, buyer):
    # buyer فیکسچر فقط phone داره، email نداره
    rows = notification_service.enqueue(
        db_session,
        user=buyer,
        event_id=None,
        template_key=NotificationTemplateKey.EVENT_REMINDER_1H,
        payload={"event_title": "تست"},
    )
    assert len(rows) == 1
    assert rows[0].channel == NotificationChannel.SMS
    assert rows[0].destination == buyer.phone


def test_notify_registration_complete_free_uses_registration_template(
    db_session, published_event, buyer, free_ticket_type
):
    session = published_event.sessions[0]
    order = create_order(
        db_session, buyer.id, OrderCreateIn(ticket_type_id=free_ticket_type.id, session_id=session.id)
    )
    complete_order(db_session, order)
    registration = db_session.query(Registration).filter_by(user_id=buyer.id).one()

    rows = notification_service.notify_registration_complete(
        db_session,
        user=buyer,
        event=published_event,
        session=session,
        ticket_type=free_ticket_type,
        registration=registration,
    )
    assert rows[0].template_key == NotificationTemplateKey.REGISTRATION_COMPLETE
    payload = json.loads(rows[0].payload_json)
    assert payload["ticket_code"] == registration.ticket_code
    assert payload["event_title"] == published_event.title
    assert "calendar_link" in payload


def test_notify_registration_complete_paid_uses_purchase_template(
    db_session, published_event, buyer, paid_ticket_type
):
    session = published_event.sessions[0]
    order = create_order(
        db_session, buyer.id, OrderCreateIn(ticket_type_id=paid_ticket_type.id, session_id=session.id)
    )
    complete_order(db_session, order)
    registration = db_session.query(Registration).filter_by(user_id=buyer.id).one()

    rows = notification_service.notify_registration_complete(
        db_session,
        user=buyer,
        event=published_event,
        session=session,
        ticket_type=paid_ticket_type,
        registration=registration,
    )
    assert rows[0].template_key == NotificationTemplateKey.TICKET_PURCHASE_COMPLETE
    payload = json.loads(rows[0].payload_json)
    assert payload["ticket_price_formatted"] == f"{paid_ticket_type.price:,}"


def test_notify_event_reminder_creates_row(db_session, published_event, buyer):
    session = published_event.sessions[0]
    rows = notification_service.notify_event_reminder(
        db_session, user=buyer, event=published_event, session=session
    )
    assert rows[0].template_key == NotificationTemplateKey.EVENT_REMINDER_1H
    assert rows[0].event_id == published_event.id
