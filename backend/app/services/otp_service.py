"""OTPService — پیاده‌سازی دقیق جریان سند docs/event_otp_email_sms_plan_fa.md.

Generate OTP -> Hash OTP -> Save in DB -> Send -> User enters OTP ->
Hash entered OTP -> Compare -> Expire / Mark Used
"""

from __future__ import annotations

from datetime import timedelta

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.rate_limit import RateLimitExceeded, enforce_cooldown, enforce_otp_request_limits
from app.core.security import generate_otp, hash_otp, verify_otp_hash
from app.core.validators import normalize_destination
from app.models.base import utcnow
from app.models.otp_challenge import OTPChallenge, OTPChannel, OTPPurpose, OTPStatus
from app.providers.email.base import EmailProvider
from app.providers.sms.base import SmsProvider


class OTPServiceError(Exception):
    """پایه‌ی خطاهای OTPService با پیام امن (بدون افشای اطلاعات اضافه، طبق بخش ۱۶ سند)."""


class OTPRequestThrottled(OTPServiceError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("درخواست بیش از حد مجاز. کمی بعد دوباره تلاش کنید.")


class OTPVerificationFailed(OTPServiceError):
    def __init__(self, message: str = "کد وارد‌شده نامعتبر یا منقضی‌شده است"):
        super().__init__(message)


class OTPService:
    def __init__(
        self,
        db: Session,
        redis_client: Redis,
        sms_provider: SmsProvider,
        email_provider: EmailProvider,
        settings: Settings | None = None,
    ):
        self.db = db
        self.redis = redis_client
        self.sms_provider = sms_provider
        self.email_provider = email_provider
        self.settings = settings or get_settings()

    def request_otp(
        self,
        *,
        destination: str,
        channel: str,
        purpose: str,
        request_ip: str | None = None,
        user_id: int | None = None,
        event_id: int | None = None,
    ) -> OTPChallenge:
        normalized_destination = normalize_destination(destination, channel)

        try:
            enforce_cooldown(
                self.redis, normalized_destination, self.settings.otp_resend_cooldown_seconds
            )
            enforce_otp_request_limits(
                self.redis,
                destination=normalized_destination,
                request_ip=request_ip,
                user_id=user_id,
                max_per_hour=self.settings.otp_max_requests_per_hour,
                max_per_day=self.settings.otp_max_requests_per_day,
                ip_max_per_10_minutes=self.settings.otp_ip_max_requests_per_10_minutes,
            )
        except RateLimitExceeded as exc:
            raise OTPRequestThrottled(retry_after=exc.retry_after) from exc

        otp = generate_otp(self.settings.otp_length)
        now = utcnow()

        provider_name = (
            self.sms_provider.name if channel == OTPChannel.SMS.value else self.email_provider.name
        )

        challenge = OTPChallenge(
            user_id=user_id,
            event_id=event_id,
            destination=normalized_destination,
            channel=OTPChannel(channel),
            purpose=OTPPurpose(purpose),
            otp_hash="",  # موقتاً خالی؛ بعد از گرفتن id واقعی محاسبه می‌شود
            expires_at=now + timedelta(seconds=self.settings.otp_expiration_seconds),
            max_attempts=self.settings.otp_max_attempts,
            status=OTPStatus.PENDING,
            last_sent_at=now,
            request_ip=request_ip,
            provider=provider_name,
            created_by="user",
        )
        self.db.add(challenge)
        self.db.flush()  # برای گرفتن id بدون commit نهایی

        challenge.otp_hash = hash_otp(otp, str(challenge.id))
        self.db.commit()
        self.db.refresh(challenge)

        self._send_otp(channel, normalized_destination, otp, challenge)

        return challenge

    def _send_otp(self, channel: str, destination: str, otp: str, challenge: OTPChallenge) -> None:
        expiry_minutes = self.settings.otp_expiration_seconds // 60
        if channel == OTPChannel.SMS.value:
            message = f"کد تأیید رویا ایونت: {otp}\nاین کد تا {expiry_minutes} دقیقه معتبر است."
            result = self.sms_provider.send(destination, message)
        else:
            subject = "کد تأیید ثبت‌نام در رویا ایونت"
            html = (
                f"<div dir='rtl'>کد تأیید شما: <b>{otp}</b><br/>"
                f"این کد تا {expiry_minutes} دقیقه معتبر است.<br/>"
                "اگر این درخواست توسط شما انجام نشده، این پیام را نادیده بگیرید.</div>"
            )
            result = self.email_provider.send(destination, subject, html)

        challenge.provider_message_id = result.provider_message_id
        self.db.commit()

    def verify_otp(self, challenge_id: int, otp: str) -> OTPChallenge:
        challenge = self.db.get(OTPChallenge, challenge_id)
        if challenge is None:
            raise OTPVerificationFailed()

        now = utcnow()

        if challenge.status != OTPStatus.PENDING:
            raise OTPVerificationFailed()

        if now > challenge.expires_at:
            challenge.status = OTPStatus.EXPIRED
            self.db.commit()
            raise OTPVerificationFailed()

        if challenge.attempt_count >= challenge.max_attempts:
            challenge.status = OTPStatus.LOCKED
            self.db.commit()
            raise OTPVerificationFailed()

        if not verify_otp_hash(otp, str(challenge.id), challenge.otp_hash):
            challenge.attempt_count += 1
            if challenge.attempt_count >= challenge.max_attempts:
                challenge.status = OTPStatus.LOCKED
            self.db.commit()
            raise OTPVerificationFailed()

        challenge.status = OTPStatus.VERIFIED
        challenge.used_at = now
        self.db.commit()
        self.db.refresh(challenge)
        return challenge

    def resend_otp(self, challenge_id: int) -> OTPChallenge:
        old = self.db.get(OTPChallenge, challenge_id)
        if old is None:
            raise OTPVerificationFailed()
        if old.status == OTPStatus.PENDING:
            old.status = OTPStatus.CANCELLED
            self.db.commit()

        return self.request_otp(
            destination=old.destination,
            channel=old.channel.value,
            purpose=old.purpose.value,
            request_ip=old.request_ip,
            user_id=old.user_id,
            event_id=old.event_id,
        )
