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
    # طبق fallback بخش ۱۰ architecture.md: بدون هیچ رویداد is_featured،
    # همین رویداد باید جای‌گزین بخش «ویژه» هم بشه
    assert event_id in [e["id"] for e in body["featured_events"]]


def test_home_sections_excludes_draft_event(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.get("/api/v1/home/sections")
    body = resp.json()
    sections = ("popular_events", "latest_events", "featured_events")
    all_ids = {e["id"] for section in sections for e in body[section]}
    assert event_id not in all_ids


def test_home_sections_includes_popular_organizer(
    client, leaf_category, auth_headers, organizer, buyer_auth_headers
):
    client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)

    resp = client.get("/api/v1/home/sections")
    organizers = resp.json()["popular_organizers"]
    assert any(o["id"] == organizer.id and o["follower_count"] == 1 for o in organizers)


def test_home_sections_is_cached(client, leaf_category, auth_headers):
    first = client.get("/api/v1/home/sections")
    assert first.json()["latest_events"] == []

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    client.post(f"/api/v1/events/{create_resp.json()['id']}/publish", headers=auth_headers)

    second = client.get("/api/v1/home/sections")
    assert second.json()["latest_events"] == [], "باید نتیجه‌ی قبلی از کش Redis برگرده، نه کوئری تازه"
