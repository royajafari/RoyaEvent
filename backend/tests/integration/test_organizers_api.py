def test_get_organizer_profile_includes_events_and_follow_state(
    client, published_event, organizer, buyer_auth_headers
):
    anon_resp = client.get(f"/api/v1/organizers/{organizer.id}")
    assert anon_resp.status_code == 200
    body = anon_resp.json()
    assert body["name"] == organizer.full_name
    assert body["is_following"] is False
    assert any(e["id"] == published_event.id for e in body["events"])

    client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)
    follower_resp = client.get(f"/api/v1/organizers/{organizer.id}", headers=buyer_auth_headers)
    assert follower_resp.json()["is_following"] is True
    assert follower_resp.json()["follower_count"] == 1


def test_get_organizer_profile_excludes_draft_events(client, leaf_category, auth_headers, organizer):
    from datetime import datetime, timedelta

    client.post(
        "/api/v1/events",
        json={
            "title": "رویداد پیش‌نویس",
            "description": "توضیحات",
            "category_id": leaf_category.id,
            "format": "online",
            "online_platform_name": "SkyRoom",
            "visibility": "public",
            "sessions": [
                {
                    "starts_at": (datetime.now() + timedelta(hours=48)).isoformat(),
                    "duration_minutes": 60,
                }
            ],
        },
        headers=auth_headers,
    )

    resp = client.get(f"/api/v1/organizers/{organizer.id}")
    titles = [e["title"] for e in resp.json()["events"]]
    assert "رویداد پیش‌نویس" not in titles


def test_get_organizer_profile_not_found_404(client):
    resp = client.get("/api/v1/organizers/999999")
    assert resp.status_code == 404
