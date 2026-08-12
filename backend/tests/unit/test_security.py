from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_token,
    generate_otp,
    hash_otp,
    verify_otp_hash,
)


def test_generate_otp_has_correct_length_and_is_numeric():
    otp = generate_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()


def test_generate_otp_is_not_trivially_constant():
    otps = {generate_otp(6) for _ in range(20)}
    assert len(otps) > 1


def test_hash_otp_is_deterministic_for_same_salt():
    assert hash_otp("123456", "salt-1") == hash_otp("123456", "salt-1")


def test_hash_otp_differs_per_salt():
    assert hash_otp("123456", "salt-1") != hash_otp("123456", "salt-2")


def test_verify_otp_hash_roundtrip():
    h = hash_otp("654321", "challenge-42")
    assert verify_otp_hash("654321", "challenge-42", h) is True
    assert verify_otp_hash("000000", "challenge-42", h) is False


def test_access_token_roundtrip():
    token = create_access_token(user_id=7)
    payload = decode_token(token)
    assert payload["sub"] == "7"
    assert payload["type"] == "access"


def test_decode_token_rejects_expired():
    settings = get_settings()
    expired_payload = {
        "sub": "1",
        "type": "access",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(ValueError):
        decode_token(expired_token)


def test_decode_token_rejects_tampered_signature():
    token = create_access_token(user_id=1) + "tampered"
    with pytest.raises(ValueError):
        decode_token(token)
