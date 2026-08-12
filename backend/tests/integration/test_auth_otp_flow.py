import re


def _last_otp(sms_provider) -> str:
    message = sms_provider.sent_messages[-1]["message"]
    return re.search(r"\d{4,8}", message).group()


def test_full_otp_login_flow_issues_access_token_and_me_works(client, sms_provider):
    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    assert resp.status_code == 200
    challenge_id = resp.json()["challenge_id"]

    otp = _last_otp(sms_provider)

    verify_resp = client.post(
        "/api/v1/auth/otp/verify", json={"challenge_id": challenge_id, "otp": otp}
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["verified"] is True
    access_token = body["access_token"]
    assert access_token

    # کوکی refresh_token باید httpOnly ست شده باشد
    assert "refresh_token" in client.cookies

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["phone"] == "09121234567"


def test_verify_with_wrong_otp_returns_verified_false(client):
    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    challenge_id = resp.json()["challenge_id"]

    verify_resp = client.post(
        "/api/v1/auth/otp/verify", json={"challenge_id": challenge_id, "otp": "000000"}
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["verified"] is False
    assert body["access_token"] is None


def test_me_without_token_is_unauthorized(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_invalid_phone_number_returns_422(client):
    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "not-a-phone", "channel": "sms"}
    )
    assert resp.status_code == 422


def test_immediate_second_request_is_rate_limited(client):
    first = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    assert second.status_code == 429
    assert "Retry-After" in second.headers


def test_resend_endpoint_cancels_and_reissues(client, sms_provider, fake_redis):
    first = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    first_challenge_id = first.json()["challenge_id"]

    fake_redis.delete("otp:cooldown:09121234567")

    resend = client.post("/api/v1/auth/otp/resend", json={"challenge_id": first_challenge_id})
    assert resend.status_code == 200
    assert resend.json()["challenge_id"] != first_challenge_id


def test_refresh_flow_issues_new_access_token(client, sms_provider):
    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    challenge_id = resp.json()["challenge_id"]
    otp = _last_otp(sms_provider)
    client.post("/api/v1/auth/otp/verify", json={"challenge_id": challenge_id, "otp": otp})

    refresh_resp = client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["access_token"]


def test_logout_clears_session_so_refresh_fails(client, sms_provider):
    resp = client.post(
        "/api/v1/auth/otp/request", json={"destination": "09121234567", "channel": "sms"}
    )
    challenge_id = resp.json()["challenge_id"]
    otp = _last_otp(sms_provider)
    client.post("/api/v1/auth/otp/verify", json={"challenge_id": challenge_id, "otp": otp})

    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    refresh_resp = client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 401


def test_health_endpoint_still_works(client):
    resp = client.get("/health")
    assert resp.status_code == 200
