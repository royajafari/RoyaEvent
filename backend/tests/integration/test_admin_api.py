from datetime import datetime, timedelta


def _future_iso(hours: int) -> str:
    return (datetime.now() + timedelta(hours=hours)).isoformat()


def _event_payload(category_id: int, **overrides) -> dict:
    payload = {
        "title": "کارگاه آموزشی هوش مصنوعی",
        "description": "توضیحات کامل کارگاه",
        "category_id": category_id,
        "format": "online",
        "online_platform_name": "SkyRoom",
        "visibility": "public",
        "sessions": [{"starts_at": _future_iso(48), "duration_minutes": 90}],
    }
    payload.update(overrides)
    return payload


def test_admin_endpoints_reject_non_admin(client, buyer_auth_headers):
    assert client.get("/api/v1/admin/events", headers=buyer_auth_headers).status_code == 403
    assert client.get("/api/v1/admin/users", headers=buyer_auth_headers).status_code == 403
    assert client.get("/api/v1/admin/categories", headers=buyer_auth_headers).status_code == 403
    assert client.get("/api/v1/admin/audit-log", headers=buyer_auth_headers).status_code == 403


def test_admin_endpoints_reject_anonymous(client):
    assert client.get("/api/v1/admin/events").status_code == 401


def test_admin_list_events_includes_draft(client, leaf_category, auth_headers, admin_auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.get("/api/v1/admin/events", headers=admin_auth_headers)
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert event_id in ids
    assert next(e for e in resp.json() if e["id"] == event_id)["status"] == "draft"


def test_admin_delete_event_soft_deletes_and_logs_action(
    client, published_event, admin_auth_headers, db_session
):
    """تصمیم کاربر: «حذف کامل» ادمین یه soft delete است، نه حذف واقعی ردیف —
    برای این‌که هم دیتا برای بازیابی/بررسی بمونه هم لاگ اقدام بی‌معنی نشه."""
    from app.models.admin_audit_log import AdminAuditLog
    from app.models.event import Event

    resp = client.delete(f"/api/v1/admin/events/{published_event.id}", headers=admin_auth_headers)
    assert resp.status_code == 200

    db_session.refresh(published_event)
    assert db_session.get(Event, published_event.id) is not None
    assert published_event.deleted_at is not None

    log_entry = (
        db_session.query(AdminAuditLog)
        .filter_by(action="delete_event", target_id=published_event.id)
        .first()
    )
    assert log_entry is not None


def test_admin_delete_event_hides_it_from_public_and_admin_listings(
    client, published_event, admin_auth_headers
):
    resp = client.delete(f"/api/v1/admin/events/{published_event.id}", headers=admin_auth_headers)
    assert resp.status_code == 200

    public_resp = client.get(f"/api/v1/events/{published_event.slug}")
    assert public_resp.status_code == 404

    admin_list_resp = client.get("/api/v1/admin/events", headers=admin_auth_headers)
    ids = [e["id"] for e in admin_list_resp.json()]
    assert published_event.id not in ids


def test_admin_delete_event_with_orders_keeps_orders_intact(
    client, published_event, free_ticket_type, buyer_auth_headers, admin_auth_headers, db_session
):
    """برخلاف رفتار قبلی (حذف واقعی + cascade)، الان سفارش/ثبت‌نام مرتبط
    نباید دست بخورن — چون خود رویداد هم واقعاً حذف نمی‌شه."""
    from app.models.order import Registration

    order_resp = client.post(
        "/api/v1/orders",
        json={"ticket_type_id": free_ticket_type.id, "session_id": published_event.sessions[0].id},
        headers=buyer_auth_headers,
    )
    order_id = order_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)

    resp = client.delete(f"/api/v1/admin/events/{published_event.id}", headers=admin_auth_headers)
    assert resp.status_code == 200

    registrations = db_session.query(Registration).filter_by(event_id=published_event.id).all()
    assert len(registrations) == 1


def test_admin_toggle_event_featured(client, published_event, admin_auth_headers):
    resp = client.patch(
        f"/api/v1/admin/events/{published_event.id}/feature",
        json={"is_featured": True},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_featured"] is True

    resp = client.patch(
        f"/api/v1/admin/events/{published_event.id}/feature",
        json={"is_featured": False},
        headers=admin_auth_headers,
    )
    assert resp.json()["is_featured"] is False


def test_admin_cannot_suspend_self(client, admin_auth_headers, admin_user):
    resp = client.patch(
        f"/api/v1/admin/users/{admin_user.id}/suspend",
        json={"suspended": True},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 400


def test_admin_suspend_user_blocks_login_and_existing_token(
    client, buyer, buyer_auth_headers, admin_auth_headers
):
    # قبل از تعلیق، توکن باید کار کنه
    assert client.get("/api/v1/auth/me", headers=buyer_auth_headers).status_code == 200

    resp = client.patch(
        f"/api/v1/admin/users/{buyer.id}/suspend",
        json={"suspended": True, "reason": "تست"},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspended"

    # توکن قبلی (که هنوز منقضی نشده) هم باید دیگه کار نکنه
    assert client.get("/api/v1/auth/me", headers=buyer_auth_headers).status_code == 401


def test_admin_category_crud(client, admin_auth_headers):
    create_resp = client.post(
        "/api/v1/admin/categories", json={"name": "دسته‌ی تست", "parent_id": None}, headers=admin_auth_headers
    )
    assert create_resp.status_code == 201
    category_id = create_resp.json()["id"]

    update_resp = client.patch(
        f"/api/v1/admin/categories/{category_id}",
        json={"name": "دسته‌ی ویرایش‌شده", "parent_id": None},
        headers=admin_auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "دسته‌ی ویرایش‌شده"

    delete_resp = client.delete(f"/api/v1/admin/categories/{category_id}", headers=admin_auth_headers)
    assert delete_resp.status_code == 200


def test_admin_delete_category_with_events_fails(client, leaf_category, auth_headers, admin_auth_headers):
    client.post("/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers)

    resp = client.delete(f"/api/v1/admin/categories/{leaf_category.id}", headers=admin_auth_headers)
    assert resp.status_code == 422


def test_admin_audit_log_lists_actions(client, published_event, admin_auth_headers):
    client.patch(
        f"/api/v1/admin/events/{published_event.id}/feature",
        json={"is_featured": True},
        headers=admin_auth_headers,
    )
    resp = client.get("/api/v1/admin/audit-log", headers=admin_auth_headers)
    assert resp.status_code == 200
    actions = [entry["action"] for entry in resp.json()]
    assert "feature_event" in actions


def test_admin_notifications_reject_non_admin(client, buyer_auth_headers):
    resp = client.get("/api/v1/admin/notifications", headers=buyer_auth_headers)
    assert resp.status_code == 403


def test_admin_notifications_lists_enqueued(
    client, published_event, free_ticket_type, buyer_auth_headers, admin_auth_headers
):
    create_resp = client.post(
        "/api/v1/orders",
        json={"ticket_type_id": free_ticket_type.id, "session_id": published_event.sessions[0].id},
        headers=buyer_auth_headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_auth_headers)

    resp = client.get("/api/v1/admin/notifications", headers=admin_auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    row = body[0]
    assert row["channel"] == "sms"
    assert row["template_key"] == "registration_complete"
    assert row["event_id"] == published_event.id
    assert row["event_title"] == published_event.title
    assert row["status"] in ("pending", "sent", "failed")


def _submit_review(client, event, ticket_type, buyer_headers, db_session):
    from datetime import timedelta

    from app.models.base import utcnow

    create_resp = client.post(
        "/api/v1/orders",
        json={"ticket_type_id": ticket_type.id, "session_id": event.sessions[0].id},
        headers=buyer_headers,
    )
    order_id = create_resp.json()["id"]
    client.post(f"/api/v1/orders/{order_id}/complete", headers=buyer_headers)
    event.sessions[0].starts_at = utcnow() - timedelta(hours=2)
    db_session.commit()

    resp = client.post(
        f"/api/v1/events/{event.id}/reviews",
        json={
            "axis_content_uptodate": 5,
            "axis_instructor_mastery": 5,
            "axis_value_for_price": 5,
            "axis_experience_driven": 5,
        },
        headers=buyer_headers,
    )
    return resp.json()["id"]


def test_admin_list_reviews(
    client, published_event, free_ticket_type, buyer_auth_headers, admin_auth_headers, db_session
):
    _submit_review(client, published_event, free_ticket_type, buyer_auth_headers, db_session)

    resp = client.get("/api/v1/admin/reviews", headers=admin_auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["event_title"] == published_event.title


def test_admin_hide_review_removes_from_public_list_and_logs_action(
    client, published_event, free_ticket_type, buyer_auth_headers, admin_auth_headers, db_session
):
    review_id = _submit_review(client, published_event, free_ticket_type, buyer_auth_headers, db_session)

    resp = client.patch(
        f"/api/v1/admin/reviews/{review_id}/hide",
        json={"hidden": True, "reason": "نامناسب"},
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "hidden"

    public_list = client.get(f"/api/v1/events/{published_event.id}/reviews")
    assert public_list.json() == []

    log_resp = client.get("/api/v1/admin/audit-log", headers=admin_auth_headers)
    actions = [entry["action"] for entry in log_resp.json()]
    assert "hide_review" in actions
