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
        "instructor_names": ["استاد تست"],
        "sessions": [{"starts_at": _future_iso(48), "duration_minutes": 90}],
    }
    payload.update(overrides)
    return payload


def test_create_event_with_instructor_names_creates_instructor(client, leaf_category, auth_headers):
    resp = client.post("/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers)
    assert resp.status_code == 201
    instructors = resp.json()["instructors"]
    assert len(instructors) == 1
    assert instructors[0]["name"] == "استاد تست"


def test_reusing_instructor_name_links_same_instructor(client, leaf_category, auth_headers):
    first = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    second = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, title="یک رویداد دیگر"),
        headers=auth_headers,
    )
    first_id = first.json()["instructors"][0]["id"]
    second_id = second.json()["instructors"][0]["id"]
    assert first_id == second_id


def test_list_popular_instructors_orders_by_follower_count(
    client, leaf_category, auth_headers, buyer_auth_headers
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    instructor_id = create_resp.json()["instructors"][0]["id"]

    client.post(f"/api/v1/follows/instructors/{instructor_id}", headers=buyer_auth_headers)

    resp = client.get("/api/v1/instructors")
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["id"] == instructor_id
    assert body[0]["follower_count"] == 1


def test_get_instructor_detail_includes_events_and_follow_state(
    client, leaf_category, auth_headers, buyer_auth_headers
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    instructor_id = create_resp.json()["instructors"][0]["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    anon_resp = client.get(f"/api/v1/instructors/{instructor_id}")
    assert anon_resp.status_code == 200
    assert anon_resp.json()["is_following"] is False
    assert len(anon_resp.json()["events"]) == 1

    client.post(f"/api/v1/follows/instructors/{instructor_id}", headers=buyer_auth_headers)
    follower_resp = client.get(f"/api/v1/instructors/{instructor_id}", headers=buyer_auth_headers)
    assert follower_resp.json()["is_following"] is True


def test_get_instructor_not_found_404(client):
    resp = client.get("/api/v1/instructors/999999")
    assert resp.status_code == 404


def test_instructor_starts_unclaimed(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    instructor_id = create_resp.json()["instructors"][0]["id"]

    resp = client.get(f"/api/v1/instructors/{instructor_id}")
    assert resp.json()["is_claimed"] is False
    assert resp.json()["is_owned_by_me"] is False


def test_claim_instructor_succeeds(client, leaf_category, auth_headers, buyer_auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    instructor_id = create_resp.json()["instructors"][0]["id"]

    resp = client.post(f"/api/v1/instructors/{instructor_id}/claim", headers=buyer_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_claimed"] is True
    assert resp.json()["is_owned_by_me"] is True

    # از دید یه کاربر دیگه (یا ناشناس)، claim شده هست ولی owned_by_me نه
    other_resp = client.get(f"/api/v1/instructors/{instructor_id}", headers=auth_headers)
    assert other_resp.json()["is_claimed"] is True
    assert other_resp.json()["is_owned_by_me"] is False


def test_claim_already_claimed_instructor_rejected(
    client, leaf_category, auth_headers, buyer_auth_headers
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    instructor_id = create_resp.json()["instructors"][0]["id"]

    client.post(f"/api/v1/instructors/{instructor_id}/claim", headers=buyer_auth_headers)
    second_attempt = client.post(f"/api/v1/instructors/{instructor_id}/claim", headers=auth_headers)
    assert second_attempt.status_code == 422


def test_claim_instructor_requires_complete_profile(client, leaf_category, auth_headers, db_session):
    from app.models.user import User

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    instructor_id = create_resp.json()["instructors"][0]["id"]

    nameless = User(phone="09399999998")
    db_session.add(nameless)
    db_session.commit()
    db_session.refresh(nameless)

    from app.services.auth_service import AuthService

    tokens = AuthService(db_session).issue_token_pair(nameless)
    headers = {"Authorization": f"Bearer {tokens.access_token}"}

    resp = client.post(f"/api/v1/instructors/{instructor_id}/claim", headers=headers)
    assert resp.status_code == 422
