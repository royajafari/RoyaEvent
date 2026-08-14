def test_add_and_remove_favorite(client, published_event, buyer_auth_headers):
    add_resp = client.post(f"/api/v1/favorites/{published_event.id}", headers=buyer_auth_headers)
    assert add_resp.status_code == 200
    assert add_resp.json()["favorited"] is True

    list_resp = client.get("/api/v1/me/favorites", headers=buyer_auth_headers)
    assert len(list_resp.json()) == 1

    remove_resp = client.delete(f"/api/v1/favorites/{published_event.id}", headers=buyer_auth_headers)
    assert remove_resp.json()["favorited"] is False

    list_resp_after = client.get("/api/v1/me/favorites", headers=buyer_auth_headers)
    assert len(list_resp_after.json()) == 0


def test_favorite_requires_auth(client, published_event):
    resp = client.post(f"/api/v1/favorites/{published_event.id}")
    assert resp.status_code == 401


def test_favorite_unknown_event_404(client, buyer_auth_headers):
    resp = client.post("/api/v1/favorites/999999", headers=buyer_auth_headers)
    assert resp.status_code == 404


def test_follow_and_unfollow_organizer(client, organizer, buyer_auth_headers):
    follow_resp = client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)
    assert follow_resp.status_code == 200
    assert follow_resp.json() == {"following": True, "follower_count": 1}

    unfollow_resp = client.delete(
        f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers
    )
    assert unfollow_resp.json() == {"following": False, "follower_count": 0}


def test_follow_unknown_organizer_404(client, buyer_auth_headers):
    resp = client.post("/api/v1/follows/organizers/999999", headers=buyer_auth_headers)
    assert resp.status_code == 404


def test_follow_and_unfollow_instructor(client, db_session, buyer_auth_headers):
    from app.models.instructor import Instructor

    instructor = Instructor(name="مدرس تست")
    db_session.add(instructor)
    db_session.commit()
    db_session.refresh(instructor)

    follow_resp = client.post(
        f"/api/v1/follows/instructors/{instructor.id}", headers=buyer_auth_headers
    )
    assert follow_resp.status_code == 200
    assert follow_resp.json()["following"] is True

    unfollow_resp = client.delete(
        f"/api/v1/follows/instructors/{instructor.id}", headers=buyer_auth_headers
    )
    assert unfollow_resp.json()["following"] is False


def test_my_follows_detail_includes_names(client, db_session, organizer, buyer_auth_headers):
    from app.models.instructor import Instructor

    instructor = Instructor(name="مدرس تست")
    db_session.add(instructor)
    db_session.commit()
    db_session.refresh(instructor)

    client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)
    client.post(f"/api/v1/follows/instructors/{instructor.id}", headers=buyer_auth_headers)

    resp = client.get("/api/v1/me/follows/details", headers=buyer_auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["organizers"] == [
        {"id": organizer.id, "name": organizer.full_name, "avatar_url": None}
    ]
    assert body["instructors"] == [{"id": instructor.id, "name": instructor.name, "avatar_url": None}]


def test_my_follows_detail_includes_organizer_avatar(
    client, db_session, organizer, buyer_auth_headers
):
    organizer.avatar_url = "http://minio.local/avatars/1/pic.jpg"
    db_session.commit()

    client.post(f"/api/v1/follows/organizers/{organizer.id}", headers=buyer_auth_headers)

    resp = client.get("/api/v1/me/follows/details", headers=buyer_auth_headers)
    assert resp.json()["organizers"][0]["avatar_url"] == organizer.avatar_url
