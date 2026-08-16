from datetime import timedelta

from app.models.base import utcnow


def _review_payload(**overrides):
    payload = {
        "axis_content_uptodate": 5,
        "axis_instructor_mastery": 4,
        "axis_value_for_price": 3,
        "axis_experience_driven": 5,
    }
    payload.update(overrides)
    return payload


def _complete_free_order(client, event, ticket_type, headers):
    create_resp = client.post(
        "/api/v1/orders",
        json={"ticket_type_id": ticket_type.id, "session_id": event.sessions[0].id},
        headers=headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=headers)


def test_submit_review_without_registration_rejected(client, published_event, buyer_auth_headers):
    resp = client.post(
        f"/api/v1/events/{published_event.id}/reviews",
        json=_review_payload(),
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 422


def test_submit_review_before_session_starts_rejected(
    client, published_event, free_ticket_type, buyer_auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)

    resp = client.post(
        f"/api/v1/events/{published_event.id}/reviews",
        json=_review_payload(),
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 422


def test_submit_review_success_and_appears_in_public_list(
    client, published_event, free_ticket_type, buyer_auth_headers, db_session
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    published_event.sessions[0].starts_at = utcnow() - timedelta(hours=2)
    db_session.commit()

    resp = client.post(
        f"/api/v1/events/{published_event.id}/reviews",
        json=_review_payload(),
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["overall_computed"] == (5 + 4 + 3 + 5) / 4

    list_resp = client.get(f"/api/v1/events/{published_event.id}/reviews")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    event_resp = client.get(f"/api/v1/events/{published_event.slug}")
    assert event_resp.json()["rating_count"] == 1


def test_get_reviews_for_unknown_event_404(client):
    resp = client.get("/api/v1/events/999999/reviews")
    assert resp.status_code == 404
