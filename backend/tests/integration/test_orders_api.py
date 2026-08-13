def _order_payload(ticket_type, session, discount_code=None):
    payload = {"ticket_type_id": ticket_type.id, "session_id": session.id}
    if discount_code:
        payload["discount_code"] = discount_code
    return payload


def test_create_order_requires_auth(client, published_event, free_ticket_type):
    resp = client.post(
        "/api/v1/orders", json=_order_payload(free_ticket_type, published_event.sessions[0])
    )
    assert resp.status_code == 401


def test_create_order_success(client, published_event, free_ticket_type, buyer_auth_headers):
    resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_create_order_invalid_ticket_type_returns_422(client, published_event, buyer_auth_headers):
    resp = client.post(
        "/api/v1/orders",
        json={"ticket_type_id": 999999, "session_id": published_event.sessions[0].id},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 422


def test_complete_order_flow(client, published_event, free_ticket_type, buyer_auth_headers):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]

    complete_resp = client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"


def test_complete_order_forbidden_for_non_owner(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]

    # auth_headers متعلق به organizer است، نه buyer که سفارش را ساخته
    resp = client.post(f"/api/v1/orders/{order_id}/complete", headers=auth_headers)
    assert resp.status_code == 403


def test_get_order_forbidden_for_non_owner(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert resp.status_code == 403


def test_my_tickets_lists_completed_registration(
    client, published_event, free_ticket_type, buyer_auth_headers
):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)

    resp = client.get("/api/v1/me/tickets", headers=buyer_auth_headers)
    assert resp.status_code == 200
    tickets = resp.json()
    assert len(tickets) == 1
    assert tickets[0]["event_title"] == published_event.title


def test_cancel_registration_flow(client, published_event, free_ticket_type, buyer_auth_headers):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)

    tickets = client.get("/api/v1/me/tickets", headers=buyer_auth_headers).json()
    registration_id = tickets[0]["registration"]["id"]

    resp = client.post(f"/api/v1/registrations/{registration_id}/cancel", headers=buyer_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_registration_forbidden_for_non_owner(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)
    tickets = client.get("/api/v1/me/tickets", headers=buyer_auth_headers).json()
    registration_id = tickets[0]["registration"]["id"]

    resp = client.post(f"/api/v1/registrations/{registration_id}/cancel", headers=auth_headers)
    assert resp.status_code == 403


def test_calendar_link_endpoint(client, published_event, free_ticket_type, buyer_auth_headers):
    create_resp = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)
    tickets = client.get("/api/v1/me/tickets", headers=buyer_auth_headers).json()
    registration_id = tickets[0]["registration"]["id"]

    resp = client.get(
        f"/api/v1/registrations/{registration_id}/calendar-link", headers=buyer_auth_headers
    )
    assert resp.status_code == 200
    assert "calendar.google.com" in resp.json()["calendar_link"]


def test_create_order_rate_limited_after_five_per_minute(
    client, published_event, free_ticket_type, buyer_auth_headers
):
    for _ in range(5):
        client.post(
            "/api/v1/orders",
            json=_order_payload(free_ticket_type, published_event.sessions[0]),
            headers=buyer_auth_headers,
        )
    sixth = client.post(
        "/api/v1/orders",
        json=_order_payload(free_ticket_type, published_event.sessions[0]),
        headers=buyer_auth_headers,
    )
    assert sixth.status_code == 429
