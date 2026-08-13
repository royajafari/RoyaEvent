def test_update_profile_success(client, auth_headers):
    resp = client.patch("/api/v1/auth/me", json={"full_name": "نام جدید"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "نام جدید"


def test_update_profile_requires_auth(client):
    resp = client.patch("/api/v1/auth/me", json={"full_name": "نام جدید"})
    assert resp.status_code == 401


def test_update_profile_rejects_empty_name(client, auth_headers):
    resp = client.patch("/api/v1/auth/me", json={"full_name": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_me_reflects_updated_name(client, auth_headers):
    client.patch("/api/v1/auth/me", json={"full_name": "نام جدید"}, headers=auth_headers)
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.json()["full_name"] == "نام جدید"


def _make_jpeg_bytes() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (200, 200), color=(50, 60, 70)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_upload_avatar_requires_auth(client):
    resp = client.post(
        "/api/v1/auth/me/avatar", files={"file": ("avatar.jpg", _make_jpeg_bytes(), "image/jpeg")}
    )
    assert resp.status_code == 401


def test_upload_avatar_rejects_non_image(client, auth_headers):
    resp = client.post(
        "/api/v1/auth/me/avatar",
        files={"file": ("evil.txt", b"not an image", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_upload_avatar_success_with_mocked_storage(client, auth_headers, monkeypatch):
    import app.api.v1.routers.auth as auth_module

    monkeypatch.setattr(
        auth_module, "upload_avatar_image", lambda user_id, jpeg_bytes: "http://minio.local/avatar.jpg"
    )

    resp = client.post(
        "/api/v1/auth/me/avatar",
        files={"file": ("avatar.jpg", _make_jpeg_bytes(), "image/jpeg")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["avatar_url"] == "http://minio.local/avatar.jpg"
