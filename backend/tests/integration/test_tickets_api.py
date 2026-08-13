def test_create_ticket_type_as_owner(client, published_event, auth_headers):
    resp = client.post(
        f"/api/v1/events/{published_event.id}/ticket-types",
        json={"name": "بلیط عادی", "pricing_model": "free"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["pricing_model"] == "free"
    assert body["price"] == 0


def test_create_ticket_type_forbidden_for_non_owner(client, published_event, buyer_auth_headers):
    resp = client.post(
        f"/api/v1/events/{published_event.id}/ticket-types",
        json={"name": "بلیط عادی", "pricing_model": "free"},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 403


def test_list_ticket_types_is_public(client, published_event, free_ticket_type):
    resp = client.get(f"/api/v1/events/{published_event.id}/ticket-types")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()]
    assert free_ticket_type.name in names


def test_create_event_discount_code_as_owner(client, published_event, auth_headers):
    resp = client.post(
        f"/api/v1/events/{published_event.id}/discount-codes",
        json={"code": "OFF10", "discount_type": "percent", "value": 10},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "OFF10"


def test_create_event_discount_code_forbidden_for_non_owner(client, published_event, buyer_auth_headers):
    resp = client.post(
        f"/api/v1/events/{published_event.id}/discount-codes",
        json={"code": "OFF10", "discount_type": "percent", "value": 10},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 403


def test_create_platform_discount_code_requires_admin(client, buyer_auth_headers):
    resp = client.post(
        "/api/v1/admin/discount-codes",
        json={"code": "PLATFORM5", "discount_type": "fixed", "value": 5000},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 403


def test_create_platform_discount_code_as_admin(client, admin_auth_headers):
    resp = client.post(
        "/api/v1/admin/discount-codes",
        json={"code": "PLATFORM5", "discount_type": "fixed", "value": 5000},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "PLATFORM5"


def test_validate_discount_code_success(client, published_event, auth_headers):
    client.post(
        f"/api/v1/events/{published_event.id}/discount-codes",
        json={"code": "OFF10", "discount_type": "percent", "value": 10},
        headers=auth_headers,
    )
    resp = client.post(
        "/api/v1/discount-codes/validate",
        json={"code": "OFF10", "event_id": published_event.id},
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is True


def test_validate_discount_code_not_found(client, published_event):
    resp = client.post(
        "/api/v1/discount-codes/validate",
        json={"code": "NOPE", "event_id": published_event.id},
    )
    assert resp.status_code == 404
