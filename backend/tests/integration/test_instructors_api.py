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
