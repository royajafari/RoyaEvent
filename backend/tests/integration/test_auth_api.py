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
