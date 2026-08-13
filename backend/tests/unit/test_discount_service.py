from datetime import timedelta

from app.models.base import utcnow
from app.models.ticket import DiscountCode, DiscountType, PlatformDiscountCode
from app.services.discount_service import compute_discount_amount, find_valid_discount


def _event_code(db_session, event_id, **overrides):
    defaults = dict(
        event_id=event_id,
        code="SUMMER10",
        discount_type=DiscountType.PERCENT,
        value=10,
        is_active=True,
    )
    defaults.update(overrides)
    code = DiscountCode(**defaults)
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


def _platform_code(db_session, organizer, **overrides):
    defaults = dict(
        code="PLATFORM20",
        discount_type=DiscountType.FIXED,
        value=20000,
        is_active=True,
        created_by=organizer.id,
    )
    defaults.update(overrides)
    code = PlatformDiscountCode(**defaults)
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


def test_finds_event_level_code(db_session, published_event):
    _event_code(db_session, published_event.id)
    found = find_valid_discount(db_session, published_event.id, "SUMMER10")
    assert isinstance(found, DiscountCode)


def test_falls_back_to_platform_code(db_session, published_event, organizer):
    _platform_code(db_session, organizer)
    found = find_valid_discount(db_session, published_event.id, "PLATFORM20")
    assert isinstance(found, PlatformDiscountCode)


def test_unknown_code_returns_none(db_session, published_event):
    assert find_valid_discount(db_session, published_event.id, "NOT_REAL") is None


def test_inactive_code_is_rejected(db_session, published_event):
    _event_code(db_session, published_event.id, is_active=False)
    assert find_valid_discount(db_session, published_event.id, "SUMMER10") is None


def test_expired_code_is_rejected(db_session, published_event):
    _event_code(db_session, published_event.id, valid_until=utcnow() - timedelta(days=1))
    assert find_valid_discount(db_session, published_event.id, "SUMMER10") is None


def test_not_yet_valid_code_is_rejected(db_session, published_event):
    _event_code(db_session, published_event.id, valid_from=utcnow() + timedelta(days=1))
    assert find_valid_discount(db_session, published_event.id, "SUMMER10") is None


def test_maxed_out_uses_code_is_rejected(db_session, published_event):
    _event_code(db_session, published_event.id, max_uses=2, uses_count=2)
    assert find_valid_discount(db_session, published_event.id, "SUMMER10") is None


def test_compute_discount_percent():
    code = DiscountCode(discount_type=DiscountType.PERCENT, value=10)
    assert compute_discount_amount(100_000, code) == 10_000


def test_compute_discount_fixed():
    code = DiscountCode(discount_type=DiscountType.FIXED, value=15_000)
    assert compute_discount_amount(100_000, code) == 15_000


def test_compute_discount_never_exceeds_subtotal():
    code = DiscountCode(discount_type=DiscountType.FIXED, value=500_000)
    assert compute_discount_amount(100_000, code) == 100_000
