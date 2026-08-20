import re
from datetime import timedelta

import pytest

from app.models.base import utcnow
from app.models.otp_challenge import OTPChallenge, OTPStatus
from app.services.otp_service import OTPRequestThrottled, OTPVerificationFailed


def _last_otp_sent(sms_provider) -> str:
    message = sms_provider.sent_messages[-1]["message"]
    return re.search(r"\d{4,8}", message).group()


def test_request_otp_creates_pending_challenge(otp_service):
    challenge = otp_service.request_otp(
        destination="09121234567", channel="sms", purpose="login", request_ip="1.2.3.4"
    )

    assert challenge.id is not None
    assert challenge.status == OTPStatus.PENDING
    assert challenge.destination == "09121234567"
    assert challenge.otp_hash  # هرگز خالی نیست
    assert challenge.attempt_count == 0


def test_request_otp_normalizes_destination(otp_service):
    challenge = otp_service.request_otp(
        destination="+989121234567", channel="sms", purpose="login"
    )
    assert challenge.destination == "09121234567"


def test_request_otp_never_returns_raw_otp_in_challenge(otp_service, sms_provider):
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    otp = _last_otp_sent(sms_provider)
    assert otp not in challenge.otp_hash


def test_verify_otp_success_flow(otp_service, sms_provider):
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    otp = _last_otp_sent(sms_provider)

    verified = otp_service.verify_otp(challenge.id, otp)
    assert verified.status == OTPStatus.VERIFIED
    assert verified.used_at is not None


def test_verify_otp_wrong_code_increments_attempt_and_fails(otp_service):
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")

    with pytest.raises(OTPVerificationFailed):
        otp_service.verify_otp(challenge.id, "000000")

    refreshed = otp_service.db.get(OTPChallenge, challenge.id)
    assert refreshed.attempt_count == 1
    assert refreshed.status == OTPStatus.PENDING


def test_verify_otp_locks_after_max_attempts(otp_service):
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    max_attempts = challenge.max_attempts

    for _ in range(max_attempts):
        with pytest.raises(OTPVerificationFailed):
            otp_service.verify_otp(challenge.id, "000000")

    refreshed = otp_service.db.get(OTPChallenge, challenge.id)
    assert refreshed.status == OTPStatus.LOCKED

    # حتی اگر بعد از قفل‌شدن، کد درست را (فرضی) بفرستد، دیگر قبول نمی‌شود
    with pytest.raises(OTPVerificationFailed):
        otp_service.verify_otp(challenge.id, "123456")


def test_verify_otp_expired(otp_service, db_session):
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    challenge.expires_at = utcnow() - timedelta(seconds=1)
    db_session.commit()

    with pytest.raises(OTPVerificationFailed):
        otp_service.verify_otp(challenge.id, "123456")

    refreshed = otp_service.db.get(OTPChallenge, challenge.id)
    assert refreshed.status == OTPStatus.EXPIRED


def test_verify_otp_is_one_time_use(otp_service, sms_provider):
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    otp = _last_otp_sent(sms_provider)

    otp_service.verify_otp(challenge.id, otp)

    with pytest.raises(OTPVerificationFailed):
        otp_service.verify_otp(challenge.id, otp)


def test_request_otp_enforces_resend_cooldown(otp_service):
    otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")

    with pytest.raises(OTPRequestThrottled):
        otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")


def test_request_otp_enforces_hourly_limit(otp_service, fake_redis):
    settings = otp_service.settings
    # کول‌داون بین درخواست‌ها رو صفر می‌کنیم که فقط سقف ساعتی رو تست کنیم
    for _ in range(settings.otp_max_requests_per_hour):
        fake_redis.delete("otp:cooldown:09121234567")
        otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")

    fake_redis.delete("otp:cooldown:09121234567")
    with pytest.raises(OTPRequestThrottled):
        otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")


def test_request_otp_enforces_ip_limit(otp_service, fake_redis):
    settings = otp_service.settings
    for i in range(settings.otp_ip_max_requests_per_10_minutes):
        otp_service.request_otp(
            destination=f"0912123{i:04d}", channel="sms", purpose="login", request_ip="9.9.9.9"
        )

    with pytest.raises(OTPRequestThrottled):
        otp_service.request_otp(
            destination="09129999999", channel="sms", purpose="login", request_ip="9.9.9.9"
        )


def test_resend_otp_cancels_previous_and_issues_new(otp_service, fake_redis):
    first = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    fake_redis.delete("otp:cooldown:09121234567")

    second = otp_service.resend_otp(first.id)

    assert second.id != first.id
    refreshed_first = otp_service.db.get(OTPChallenge, first.id)
    assert refreshed_first.status == OTPStatus.CANCELLED
    assert second.status == OTPStatus.PENDING


def test_request_otp_via_email_channel_uses_email_provider(otp_service, email_provider):
    challenge = otp_service.request_otp(
        destination="user@example.com", channel="email", purpose="login"
    )
    assert challenge.channel.value == "email"
    assert len(email_provider.sent_messages) == 1
    assert email_provider.sent_messages[0]["to"] == "user@example.com"


def test_verify_otp_with_nonexistent_challenge_id_raises(otp_service):
    with pytest.raises(OTPVerificationFailed):
        otp_service.verify_otp(999999, "123456")


def test_resend_otp_with_nonexistent_challenge_id_raises(otp_service):
    with pytest.raises(OTPVerificationFailed):
        otp_service.resend_otp(999999)


def test_verify_otp_defensive_lock_when_attempt_count_already_at_max(otp_service, db_session):
    """مسیر دفاع در عمق: در جریان عادی، status همون لحظه‌ای که attempt_count
    به max_attempts می‌رسه LOCKED می‌شه (پس در تماس بعدی از شاخه‌ی «status !=
    PENDING» رد می‌شه، نه این شاخه). این تست مستقیم یک challenge با
    attempt_count از قبل >= max_attempts ولی status هنوز PENDING می‌سازه —
    حالتی که نباید از مسیر عادی سرویس اتفاق بیفته، ولی کد باید در برابرش هم
    مقاوم باشه (خط ۱۵۱-۱۵۵ otp_service.py)."""
    challenge = otp_service.request_otp(destination="09121234567", channel="sms", purpose="login")
    challenge.attempt_count = challenge.max_attempts
    db_session.commit()

    with pytest.raises(OTPVerificationFailed):
        otp_service.verify_otp(challenge.id, "000000")

    refreshed = otp_service.db.get(OTPChallenge, challenge.id)
    assert refreshed.status == OTPStatus.LOCKED
