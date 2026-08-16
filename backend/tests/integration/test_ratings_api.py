def test_submit_organizer_rating(client, organizer, buyer_auth_headers):
    resp = client.post(
        "/api/v1/ratings",
        json={"entity_type": "organizer", "entity_id": organizer.id, "score": 4},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["average"] == 4.0
    assert body["count"] == 1

    profile_resp = client.get(f"/api/v1/organizers/{organizer.id}", headers=buyer_auth_headers)
    assert profile_resp.json()["rating_avg"] == 4.0
    assert profile_resp.json()["rating_count"] == 1
    assert profile_resp.json()["my_rating"] == 4


def test_submit_organizer_rating_unknown_organizer_404(client, buyer_auth_headers):
    resp = client.post(
        "/api/v1/ratings",
        json={"entity_type": "organizer", "entity_id": 999999, "score": 3},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 404


def test_submit_instructor_rating(client, leaf_category, auth_headers, buyer_auth_headers):
    from datetime import datetime, timedelta

    create_resp = client.post(
        "/api/v1/events",
        json={
            "title": "کارگاه تست",
            "description": "توضیحات",
            "category_id": leaf_category.id,
            "format": "online",
            "online_platform_name": "SkyRoom",
            "instructor_names": ["مدرس تست"],
            "sessions": [
                {
                    "starts_at": (datetime.now() + timedelta(hours=48)).isoformat(),
                    "duration_minutes": 60,
                }
            ],
        },
        headers=auth_headers,
    )
    instructor_id = create_resp.json()["instructors"][0]["id"]

    resp = client.post(
        "/api/v1/ratings",
        json={"entity_type": "instructor", "entity_id": instructor_id, "score": 5},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 200

    detail_resp = client.get(f"/api/v1/instructors/{instructor_id}")
    assert detail_resp.json()["rating_avg"] == 5.0
    assert detail_resp.json()["rating_count"] == 1


def test_submit_platform_rating(client, buyer_auth_headers):
    resp = client.post(
        "/api/v1/ratings",
        json={"entity_type": "platform", "score": 5},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["average"] == 5.0


def test_submit_rating_requires_auth(client, organizer):
    resp = client.post(
        "/api/v1/ratings",
        json={"entity_type": "organizer", "entity_id": organizer.id, "score": 3},
    )
    assert resp.status_code == 401


def test_submit_rating_out_of_range_rejected(client, organizer, buyer_auth_headers):
    resp = client.post(
        "/api/v1/ratings",
        json={"entity_type": "organizer", "entity_id": organizer.id, "score": 6},
        headers=buyer_auth_headers,
    )
    assert resp.status_code == 422
