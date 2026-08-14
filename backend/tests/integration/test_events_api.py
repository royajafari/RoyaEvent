import io
from datetime import datetime, timedelta

from PIL import Image


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
        "tag_names": ["هوش‌مصنوعی"],
        "sessions": [{"starts_at": _future_iso(48), "duration_minutes": 90}],
    }
    payload.update(overrides)
    return payload


def _make_jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (300, 200), color=(10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_mp4_bytes() -> bytes:
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"


def test_create_event_requires_auth(client, leaf_category):
    resp = client.post("/api/v1/events", json=_event_payload(leaf_category.id))
    assert resp.status_code == 401


def test_create_event_success(client, leaf_category, auth_headers):
    resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "draft"
    assert body["event_code"].startswith("RE-")
    assert len(body["sessions"]) == 1


def test_create_event_requires_complete_profile(client, leaf_category, db_session):
    from app.models.user import User
    from app.services.auth_service import AuthService

    incomplete_user = User(phone="09309999999")
    db_session.add(incomplete_user)
    db_session.commit()
    db_session.refresh(incomplete_user)
    tokens = AuthService(db_session).issue_token_pair(incomplete_user)
    headers = {"Authorization": f"Bearer {tokens.access_token}"}

    resp = client.post("/api/v1/events", json=_event_payload(leaf_category.id), headers=headers)
    assert resp.status_code == 422

    client.patch("/api/v1/auth/me", json={"full_name": "کاربر تازه"}, headers=headers)
    resp = client.post("/api/v1/events", json=_event_payload(leaf_category.id), headers=headers)
    assert resp.status_code == 201


def test_create_event_rejects_parent_category(client, leaf_category, auth_headers, db_session):
    from app.models.category import Category

    parent = db_session.get(Category, leaf_category.parent_id)
    resp = client.post(
        "/api/v1/events", json=_event_payload(parent.id), headers=auth_headers
    )
    assert resp.status_code == 422


def test_draft_event_not_visible_via_public_slug(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    slug = create_resp.json()["slug"]

    resp = client.get(f"/api/v1/events/{slug}")
    assert resp.status_code == 404


def test_publish_then_public_slug_works(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    slug = create_resp.json()["slug"]

    publish_resp = client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"

    public_resp = client.get(f"/api/v1/events/{slug}")
    assert public_resp.status_code == 200
    assert public_resp.json()["status"] == "published"


def test_publish_twice_fails(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    second = client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)
    assert second.status_code == 422


def test_list_events_only_shows_published_public(client, leaf_category, auth_headers):
    draft = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    ).json()
    published = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    ).json()
    client.post(f"/api/v1/events/{published['id']}/publish", headers=auth_headers)

    resp = client.get("/api/v1/events")
    ids = [e["id"] for e in resp.json()]
    assert published["id"] in ids
    assert draft["id"] not in ids


def test_list_events_featured_filter(client, leaf_category, auth_headers, db_session):
    from app.models.event import Event

    plain = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id, title="رویداد عادی"), headers=auth_headers
    ).json()
    featured = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id, title="رویداد ویژه"), headers=auth_headers
    ).json()
    client.post(f"/api/v1/events/{plain['id']}/publish", headers=auth_headers)
    client.post(f"/api/v1/events/{featured['id']}/publish", headers=auth_headers)
    db_session.query(Event).filter(Event.id == featured["id"]).update({"is_featured": True})
    db_session.commit()

    resp = client.get("/api/v1/events?featured=true")
    ids = [e["id"] for e in resp.json()]
    assert featured["id"] in ids
    assert plain["id"] not in ids


def test_list_events_sort_popular_orders_by_view_count(client, leaf_category, auth_headers, db_session):
    from app.models.event import Event

    low = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id, title="بازدید کم"), headers=auth_headers
    ).json()
    high = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id, title="بازدید زیاد"), headers=auth_headers
    ).json()
    client.post(f"/api/v1/events/{low['id']}/publish", headers=auth_headers)
    client.post(f"/api/v1/events/{high['id']}/publish", headers=auth_headers)

    db_session.query(Event).filter(Event.id == high["id"]).update({"view_count": 50})
    db_session.query(Event).filter(Event.id == low["id"]).update({"view_count": 1})
    db_session.commit()

    resp = client.get("/api/v1/events?sort=popular")
    ids = [e["id"] for e in resp.json()]
    assert ids.index(high["id"]) < ids.index(low["id"])


def test_list_my_events_shows_all_own_statuses(client, leaf_category, auth_headers):
    client.post("/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers)
    client.post("/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers)

    resp = client.get("/api/v1/events/mine", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_event_forbidden_for_non_owner(client, leaf_category, auth_headers, db_session):
    from app.models.user import User
    from app.services.auth_service import AuthService

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    other_user = User(phone="09351234567")
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)
    other_tokens = AuthService(db_session).issue_token_pair(other_user)
    other_headers = {"Authorization": f"Bearer {other_tokens.access_token}"}

    resp = client.patch(
        f"/api/v1/events/{event_id}", json={"title": "دستکاری غیرمجاز"}, headers=other_headers
    )
    assert resp.status_code == 403


def test_update_event_by_owner_succeeds(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/events/{event_id}", json={"title": "عنوان به‌روزشده"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "عنوان به‌روزشده"


def test_cancel_event(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.delete(f"/api/v1/events/{event_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_get_event_by_id_owner_only(client, leaf_category, auth_headers, db_session):
    from app.models.user import User
    from app.services.auth_service import AuthService

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    owner_resp = client.get(f"/api/v1/events/id/{event_id}", headers=auth_headers)
    assert owner_resp.status_code == 200

    other_user = User(phone="09351234567")
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)
    other_tokens = AuthService(db_session).issue_token_pair(other_user)

    other_resp = client.get(
        f"/api/v1/events/id/{event_id}",
        headers={"Authorization": f"Bearer {other_tokens.access_token}"},
    )
    assert other_resp.status_code == 403


def test_private_event_not_visible_via_slug_but_visible_via_token(
    client, leaf_category, auth_headers, db_session
):
    from app.models.event import Event

    create_resp = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, visibility="private"),
        headers=auth_headers,
    )
    body = create_resp.json()
    event_id = body["id"]
    slug = body["slug"]

    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    assert client.get(f"/api/v1/events/{slug}").status_code == 404

    # private_access_token عمداً در schema عمومی برنمی‌گردد؛ مستقیم از DB می‌خوانیم
    token = db_session.get(Event, event_id).private_access_token
    assert token is not None

    token_resp = client.get(f"/api/v1/events/private/{token}")
    assert token_resp.status_code == 200
    assert token_resp.json()["id"] == event_id

    assert client.get("/api/v1/events/private/wrong-token").status_code == 404


def test_related_events_excludes_self_and_unpublished(client, leaf_category, auth_headers):
    first = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    ).json()
    second = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    ).json()
    client.post(f"/api/v1/events/{first['id']}/publish", headers=auth_headers)
    client.post(f"/api/v1/events/{second['id']}/publish", headers=auth_headers)

    resp = client.get(f"/api/v1/events/{first['id']}/related")
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert first["id"] not in ids
    assert second["id"] in ids


def test_categories_endpoint_lists_seeded_tree(client, leaf_category):
    resp = client.get("/api/v1/events/categories")
    assert resp.status_code == 200
    slugs = {c["slug"] for c in resp.json()}
    assert "ai" in slugs
    assert "technology" in slugs


def test_banner_upload_rejects_non_image(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{event_id}/banner",
        files={"file": ("evil.txt", b"not an image", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_banner_upload_success_with_mocked_storage(
    client, leaf_category, auth_headers, monkeypatch
):
    import app.api.v1.routers.events as events_module

    monkeypatch.setattr(
        events_module, "upload_banner_image", lambda event_id, jpeg_bytes: "http://minio.local/x.jpg"
    )

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{event_id}/banner",
        files={"file": ("banner.jpg", _make_jpeg_bytes(), "image/jpeg")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["banner_url"] == "http://minio.local/x.jpg"


def test_banner_upload_forbidden_for_non_owner(client, leaf_category, auth_headers, db_session):
    from app.models.user import User
    from app.services.auth_service import AuthService

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    other_user = User(phone="09351234567")
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)
    other_tokens = AuthService(db_session).issue_token_pair(other_user)

    resp = client.post(
        f"/api/v1/events/{event_id}/banner",
        files={"file": ("banner.jpg", _make_jpeg_bytes(), "image/jpeg")},
        headers={"Authorization": f"Bearer {other_tokens.access_token}"},
    )
    assert resp.status_code == 403


def test_promo_video_upload_rejects_non_video(client, leaf_category, auth_headers):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{event_id}/promo-video",
        files={"file": ("evil.txt", b"not a video", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_promo_video_upload_success_with_mocked_storage(
    client, leaf_category, auth_headers, monkeypatch
):
    import app.api.v1.routers.events as events_module

    monkeypatch.setattr(
        events_module,
        "upload_promo_video",
        lambda event_id, raw, content_type: "http://minio.local/x.mp4",
    )

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{event_id}/promo-video",
        files={"file": ("promo.mp4", _make_mp4_bytes(), "video/mp4")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["promo_video_url"] == "http://minio.local/x.mp4"


def test_promo_video_upload_forbidden_for_non_owner(client, leaf_category, auth_headers, db_session):
    from app.models.user import User
    from app.services.auth_service import AuthService

    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    other_user = User(phone="09351234568")
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)
    other_tokens = AuthService(db_session).issue_token_pair(other_user)

    resp = client.post(
        f"/api/v1/events/{event_id}/promo-video",
        files={"file": ("promo.mp4", _make_mp4_bytes(), "video/mp4")},
        headers={"Authorization": f"Bearer {other_tokens.access_token}"},
    )
    assert resp.status_code == 403
