import pytest

from app.core.validators import (
    InvalidEmail,
    InvalidPhoneNumber,
    normalize_iranian_mobile,
    validate_email_format,
)


@pytest.mark.parametrize(
    "raw",
    ["09121234567", "+989121234567", "00989121234567", "989121234567", "9121234567"],
)
def test_normalize_iranian_mobile_accepts_valid_formats(raw):
    assert normalize_iranian_mobile(raw) == "09121234567"


@pytest.mark.parametrize("raw", ["0812345678", "091212345", "not-a-phone", "0812123456778"])
def test_normalize_iranian_mobile_rejects_invalid(raw):
    with pytest.raises(InvalidPhoneNumber):
        normalize_iranian_mobile(raw)


def test_normalize_iranian_mobile_rejects_unknown_prefix():
    with pytest.raises(InvalidPhoneNumber):
        normalize_iranian_mobile("09401234567")


def test_validate_email_format_accepts_valid():
    assert validate_email_format("User@Example.com") == "user@example.com"


@pytest.mark.parametrize("raw", ["not-an-email", "missing-at.com", "@nodomain", ""])
def test_validate_email_format_rejects_invalid(raw):
    with pytest.raises(InvalidEmail):
        validate_email_format(raw)
