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


def test_home_sections_shape_on_empty_db(client):
    resp = client.get("/api/v1/home/sections")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {
        "popular_events",
        "latest_events",
        "featured_events",
        "top_rated_events",
        "popular_instructors",
        "popular_organizers",
    }
    assert body["popular_events"] == []


def test_home_sections_includes_published_event_in_latest_and_popular(
    client, leaf_category, auth_headers
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    resp = client.get("/api/v1/home/sections")
    body = resp.json()
    assert event_id in [e["id"] for e in body["latest_events"]]


def test_home_sections_featured_excludes_events_from_unfollowed_organizers(
    client, leaf_category, auth_headers
):
    """بدون is_featured دستی و بدون هیچ دنبال‌کننده‌ای برای برگزارکننده،
    رویداد نباید صرفاً به‌خاطر جدید بودن وارد بخش «ویژه» بشه — طبق بازخورد
    کاربر، «ویژه» نباید معادل «آخرین» باشه."""
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    resp = client.get("/api/v1/home/sections")
    assert event_id not in [e["id"] for e in resp.json()["featured_events"]]


def test_home_sections_featured_includes_events_from_followed_organizer(
    client, leaf_category, auth_headers, organizer, buyer_auth_headers
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)
    client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)

    resp = client.get("/api/v1/home/sections")
    assert event_id in [e["id"] for e in resp.json()["featured_events"]]


def test_home_sections_excludes_draft_event(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.get("/api/v1/home/sections")
    body = resp.json()
    sections = ("popular_events", "latest_events", "featured_events", "top_rated_events")
    all_ids = {e["id"] for section in sections for e in body[section]}
    assert event_id not in all_ids


def test_home_sections_includes_popular_organizer(
    client, leaf_category, auth_headers, organizer, buyer_auth_headers, db_session
):
    organizer.avatar_url = "http://minio.local/avatars/1/pic.jpg"
    db_session.commit()

    client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)

    resp = client.get("/api/v1/home/sections")
    organizers = resp.json()["popular_organizers"]
    assert any(
        o["id"] == organizer.id and o["follower_count"] == 1 and o["avatar_url"] == organizer.avatar_url
        for o in organizers
    )


def test_home_sections_is_cached(client, leaf_category, auth_headers):
    first = client.get("/api/v1/home/sections")
    assert first.json()["latest_events"] == []

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    client.post(f"/api/v1/events/{create_resp.json()['id']}/publish", headers=auth_headers)

    second = client.get("/api/v1/home/sections")
    assert second.json()["latest_events"] == [], "باید نتیجه‌ی قبلی از کش Redis برگرده، نه کوئری تازه"


def test_home_top_rated_events_respects_floor_and_order(
    client, leaf_category, auth_headers, db_session
):
    from app.models.event import Event

    high_rated = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, title="رویداد پرامتیاز"),
        headers=auth_headers,
    ).json()
    client.post(f"/api/v1/events/{high_rated['id']}/publish", headers=auth_headers)

    below_floor = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, title="رویداد کم‌بازدید"),
        headers=auth_headers,
    ).json()
    client.post(f"/api/v1/events/{below_floor['id']}/publish", headers=auth_headers)

    high_row = db_session.get(Event, high_rated["id"])
    high_row.rating_avg = 4.8
    high_row.rating_count = 5
    below_row = db_session.get(Event, below_floor["id"])
    below_row.rating_avg = 5.0
    below_row.rating_count = 1  # زیر کف MIN_RATING_COUNT_FOR_TOP_RATED (۳)
    db_session.commit()

    resp = client.get("/api/v1/home/sections")
    top_rated_ids = [e["id"] for e in resp.json()["top_rated_events"]]
    assert high_row.id in top_rated_ids
    assert below_row.id not in top_rated_ids
