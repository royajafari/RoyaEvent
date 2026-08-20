import pytest
from starlette.requests import Request

from app.core.rate_limit import RateLimitExceeded, enforce_cooldown, enforce_otp_request_limits
from app.core.rate_limit_middleware import rate_limit_key
from app.core.security import create_access_token


def _make_request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "headers": raw_headers,
        "client": ("3.4.5.6", 12345),
    }
    return Request(scope)


def test_enforce_cooldown_blocks_immediate_repeat(fake_redis):
    enforce_cooldown(fake_redis, "09121234567", cooldown_seconds=60)
    with pytest.raises(RateLimitExceeded):
        enforce_cooldown(fake_redis, "09121234567", cooldown_seconds=60)


def test_enforce_cooldown_allows_different_destination(fake_redis):
    enforce_cooldown(fake_redis, "09121234567", cooldown_seconds=60)
    # مقصد متفاوت نباید تحت تأثیر cooldown مقصد اول باشه
    enforce_cooldown(fake_redis, "09129999999", cooldown_seconds=60)


def test_enforce_otp_request_limits_blocks_after_hourly_cap(fake_redis):
    for _ in range(3):
        enforce_otp_request_limits(
            fake_redis,
            destination="09121234567",
            request_ip=None,
            user_id=None,
            max_per_hour=3,
            max_per_day=100,
            ip_max_per_10_minutes=100,
        )
    with pytest.raises(RateLimitExceeded):
        enforce_otp_request_limits(
            fake_redis,
            destination="09121234567",
            request_ip=None,
            user_id=None,
            max_per_hour=3,
            max_per_day=100,
            ip_max_per_10_minutes=100,
        )


def test_enforce_otp_request_limits_per_user_branch(fake_redis):
    """شاخه‌ی user_id (خط ۶۶ rate_limit.py) — سقف جداگانه‌ی ساعتی به‌ازای
    کاربر لاگین‌کرده، مستقل از سقف destination."""
    for i in range(2):
        enforce_otp_request_limits(
            fake_redis,
            destination=f"0912000{i:04d}",
            request_ip=None,
            user_id=42,
            max_per_hour=2,
            max_per_day=100,
            ip_max_per_10_minutes=100,
        )
    with pytest.raises(RateLimitExceeded):
        enforce_otp_request_limits(
            fake_redis,
            destination="09120009999",
            request_ip=None,
            user_id=42,
            max_per_hour=2,
            max_per_day=100,
            ip_max_per_10_minutes=100,
        )


def test_rate_limit_key_anonymous_uses_ip(fake_redis):
    request = _make_request()
    assert rate_limit_key(request) == "ip:3.4.5.6"


def test_rate_limit_key_authenticated_uses_user_id():
    token = create_access_token(user_id=77)
    request = _make_request({"Authorization": f"Bearer {token}"})
    assert rate_limit_key(request) == "user:77"


def test_rate_limit_key_falls_back_to_ip_on_garbage_token():
    request = _make_request({"Authorization": "Bearer not-a-real-jwt"})
    assert rate_limit_key(request) == "ip:3.4.5.6"
