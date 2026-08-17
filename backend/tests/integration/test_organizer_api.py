def _complete_free_order(client, event, ticket_type, headers):
    create_resp = client.post(
        "/api/v1/orders",
        json={"ticket_type_id": ticket_type.id, "session_id": event.sessions[0].id},
        headers=headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=headers)


def test_list_attendees_as_owner(client, published_event, free_ticket_type, buyer_auth_headers, auth_headers):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)

    resp = client.get(f"/api/v1/organizer/events/{published_event.id}/attendees", headers=auth_headers)
    assert resp.status_code == 200
    attendees = resp.json()
    assert len(attendees) == 1
    assert attendees[0]["status"] == "confirmed"


def test_list_attendees_forbidden_for_non_owner(client, published_event, buyer_auth_headers):
    resp = client.get(
        f"/api/v1/organizer/events/{published_event.id}/attendees", headers=buyer_auth_headers
    )
    assert resp.status_code == 403


def test_remove_attendee_as_owner(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    attendees = client.get(
        f"/api/v1/organizer/events/{published_event.id}/attendees", headers=auth_headers
    ).json()
    registration_id = attendees[0]["registration_id"]

    resp = client.delete(
        f"/api/v1/organizer/events/{published_event.id}/attendees/{registration_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_remove_attendee_forbidden_for_non_owner(
    client, published_event, free_ticket_type, buyer_auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    resp = client.delete(
        f"/api/v1/organizer/events/{published_event.id}/attendees/1", headers=buyer_auth_headers
    )
    assert resp.status_code == 403


def test_export_attendees_csv(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)

    resp = client.get(
        f"/api/v1/organizer/events/{published_event.id}/attendees/export", headers=auth_headers
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]
    body = resp.text
    assert "نام" in body
    assert free_ticket_type.name in body
    # بدون BOM، اکسل روی ویندوز UTF-8 رو با codepage محلی می‌خونه و متن
    # فارسی رو illegible می‌کنه — این پیشوند اجباریه.
    assert body.startswith("﻿")
    # بدون فرمول ="..."، اکسل شماره موبایل رو عدد فرض می‌کنه و صفر
    # ابتدایی‌ش رو حذف/notation علمی نشون می‌ده. csv.reader استفاده می‌شه
    # (نه substring خام) چون csv.writer نقل‌قول‌های داخل فرمول رو طبق
    # قاعده‌ی استاندارد CSV دوبل می‌کنه.
    import csv as csv_module
    import io

    rows = list(csv_module.reader(io.StringIO(body.removeprefix("﻿"))))
    assert rows[1][1] == '="09351234567"'


def test_check_in_attendee_as_owner(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    attendees = client.get(
        f"/api/v1/organizer/events/{published_event.id}/attendees", headers=auth_headers
    ).json()
    ticket_code = attendees[0]["ticket_code"]
    assert attendees[0]["checked_in_at"] is None

    resp = client.post(
        f"/api/v1/organizer/events/{published_event.id}/checkin",
        json={"ticket_code": ticket_code},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "checked_in"
    assert body["checked_in_at"] is not None


def test_check_in_unknown_code_rejected(client, published_event, auth_headers):
    resp = client.post(
        f"/api/v1/organizer/events/{published_event.id}/checkin",
        json={"ticket_code": "NOTREAL123"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_check_in_twice_rejected(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    attendees = client.get(
        f"/api/v1/organizer/events/{published_event.id}/attendees", headers=auth_headers
    ).json()
    ticket_code = attendees[0]["ticket_code"]

    first = client.post(
        f"/api/v1/organizer/events/{published_event.id}/checkin",
        json={"ticket_code": ticket_code},
        headers=auth_headers,
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/organizer/events/{published_event.id}/checkin",
        json={"ticket_code": ticket_code},
        headers=auth_headers,
    )
    assert second.status_code == 422
    assert "قبلاً" in second.json()["detail"]


def test_check_in_cancelled_registration_rejected(
    client, published_event, free_ticket_type, buyer_auth_headers, auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    attendees = client.get(
        f"/api/v1/organizer/events/{published_event.id}/attendees", headers=auth_headers
    ).json()
    registration_id = attendees[0]["registration_id"]
    ticket_code = attendees[0]["ticket_code"]

    client.delete(
        f"/api/v1/organizer/events/{published_event.id}/attendees/{registration_id}",
        headers=auth_headers,
    )

    resp = client.post(
        f"/api/v1/organizer/events/{published_event.id}/checkin",
        json={"ticket_code": ticket_code},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "لغو" in resp.json()["detail"]


def test_check_in_forbidden_for_non_owner(
    client, published_event, free_ticket_type, buyer_auth_headers
):
    _complete_free_order(client, published_event, free_ticket_type, buyer_auth_headers)
    resp = client.post(
        f"/api/v1/organizer/events/{published_event.id}/checkin",
        json={"ticket_code": "ANYCODE"},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 403
