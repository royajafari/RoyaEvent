from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


# --- OTP: تولید و هش (بخش ۵ و ۶ سند OTP) ---


def generate_otp(length: int | None = None) -> str:
    """تولید OTP با secrets (CSPRNG) — نه random معمولی، طبق بخش ۵ سند."""
    n = length or settings.otp_length
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def hash_otp(otp: str, challenge_salt: str) -> str:
    """HMAC-SHA256(secret, otp + challenge_salt) — OTP خام هرگز ذخیره نمی‌شود."""
    message = f"{otp}:{challenge_salt}".encode()
    return hmac.new(settings.otp_hash_secret.encode(), message, hashlib.sha256).hexdigest()


def verify_otp_hash(otp: str, challenge_salt: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(otp, challenge_salt), expected_hash)


# --- JWT (بخش ۷ پلن) ---


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token_jwt(user_id: int, jti: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("توکن نامعتبر یا منقضی‌شده است") from exc


def new_jti() -> str:
    return uuid4().hex


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
