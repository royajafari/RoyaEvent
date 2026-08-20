import re

from app.core.metrics import (
    orders_completed_total,
    otp_failed_total,
    otp_requested_total,
    otp_verified_total,
)


def test_metrics_endpoint_exposes_default_and_custom_metrics(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "royaevent_orders_completed_total" in body
    assert "royaevent_notification_outbox_pending" in body


def test_otp_request_and_verify_increment_counters(client, sms_provider):
    before_requested = otp_requested_total.labels(channel="sms")._value.get()
    before_verified = otp_verified_total.labels(channel="sms")._value.get()

    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    challenge_id = resp.json()["challenge_id"]
    assert otp_requested_total.labels(channel="sms")._value.get() == before_requested + 1

    otp = re.search(r"\d{4,8}", sms_provider.sent_messages[-1]["message"]).group()
    client.post("/api/v1/auth/otp/verify", json={"challenge_id": challenge_id, "otp": otp})
    assert otp_verified_total.labels(channel="sms")._value.get() == before_verified + 1


def test_failed_otp_verify_increments_failed_counter(client):
    before_failed = otp_failed_total.labels(channel="sms")._value.get()

    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    challenge_id = resp.json()["challenge_id"]
    client.post("/api/v1/auth/otp/verify", json={"challenge_id": challenge_id, "otp": "000000"})

    assert otp_failed_total.labels(channel="sms")._value.get() == before_failed + 1


def test_complete_order_increments_orders_completed_counter(
    db_session, published_event, buyer, free_ticket_type
):
    from app.schemas.order import OrderCreateIn
    from app.services.order_service import complete_order, create_order

    before = orders_completed_total._value.get()
    session = published_event.sessions[0]
    order = create_order(
        db_session, buyer.id, OrderCreateIn(ticket_type_id=free_ticket_type.id, session_id=session.id)
    )
    complete_order(db_session, order)

    assert orders_completed_total._value.get() == before + 1
