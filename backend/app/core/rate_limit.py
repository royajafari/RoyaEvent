"""Rate limiting برای OTP، دقیقاً طبق docs/event_otp_email_sms_plan_fa.md (بخش ۸ و ۹).

این ماژول جدا از میان‌افزار عمومی rate-limit سایر APIها (بخش ۶ پلن) است.
"""

from __future__ import annotations

from dataclasses import dataclass

from redis import Redis


class RateLimitExceeded(Exception):
    def __init__(self, reason: str, retry_after: int):
        self.reason = reason
        self.retry_after = retry_after
        super().__init__(reason)


@dataclass(frozen=True)
class FixedWindowLimit:
    key_prefix: str
    limit: int
    window_seconds: int


def _check_fixed_window(redis_client: Redis, identifier: str, rule: FixedWindowLimit) -> None:
    key = f"{rule.key_prefix}:{identifier}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, rule.window_seconds)
    if current > rule.limit:
        ttl = redis_client.ttl(key)
        raise RateLimitExceeded(rule.key_prefix, retry_after=max(ttl, 1))


def enforce_cooldown(redis_client: Redis, destination: str, cooldown_seconds: int) -> None:
    """فاصله‌ی حداقلی بین دو درخواست OTP متوالی برای یک مقصد (SET NX EX)."""
    key = f"otp:cooldown:{destination}"
    if not redis_client.set(key, "1", nx=True, ex=cooldown_seconds):
        ttl = redis_client.ttl(key)
        raise RateLimitExceeded("cooldown", retry_after=max(ttl, 1))


def enforce_otp_request_limits(
    redis_client: Redis,
    *,
    destination: str,
    request_ip: str | None,
    user_id: int | None,
    max_per_hour: int,
    max_per_day: int,
    ip_max_per_10_minutes: int,
) -> None:
    _check_fixed_window(
        redis_client, destination, FixedWindowLimit("otp:count:hour", max_per_hour, 3600)
    )
    _check_fixed_window(
        redis_client, destination, FixedWindowLimit("otp:count:day", max_per_day, 86400)
    )
    if request_ip:
        _check_fixed_window(
            redis_client, request_ip, FixedWindowLimit("otp:count:ip10m", ip_max_per_10_minutes, 600)
        )
    if user_id is not None:
        _check_fixed_window(
            redis_client, str(user_id), FixedWindowLimit("otp:count:user1h", max_per_hour, 3600)
        )
