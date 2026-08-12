import pytest

from app.core.security import decode_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import AuthError


@pytest.fixture()
def user(db_session):
    u = User(phone="09121234567")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def test_get_or_create_user_creates_once(auth_service):
    u1 = auth_service.get_or_create_user("09121234567", "sms")
    u2 = auth_service.get_or_create_user("09121234567", "sms")
    assert u1.id == u2.id


def test_issue_token_pair_returns_valid_tokens(auth_service, user):
    pair = auth_service.issue_token_pair(user)
    access_payload = decode_token(pair.access_token)
    refresh_payload = decode_token(pair.refresh_token)
    assert access_payload["sub"] == str(user.id)
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"


def test_issue_token_pair_persists_refresh_row(auth_service, user, db_session):
    auth_service.issue_token_pair(user)
    rows = db_session.query(RefreshToken).filter_by(user_id=user.id).all()
    assert len(rows) == 1
    assert rows[0].revoked_at is None


def test_refresh_rotates_token(auth_service, user, db_session):
    first = auth_service.issue_token_pair(user)

    second = auth_service.refresh(first.refresh_token)

    assert second.refresh_token != first.refresh_token
    rows = {r.token_hash: r for r in db_session.query(RefreshToken).filter_by(user_id=user.id).all()}
    assert len(rows) == 2
    old_row = next(r for r in rows.values() if r.revoked_at is not None)
    new_row = next(r for r in rows.values() if r.revoked_at is None)
    assert old_row.replaced_by == new_row.id


def test_refresh_with_unknown_token_raises(auth_service):
    with pytest.raises(AuthError):
        auth_service.refresh("not-a-real-token")


def test_refresh_reuse_detection_revokes_family(auth_service, user, db_session):
    first = auth_service.issue_token_pair(user)
    second = auth_service.refresh(first.refresh_token)
    third = auth_service.refresh(second.refresh_token)

    # حالا دوباره از توکن اول (که قبلاً چرخانده و باطل شده) استفاده می‌کنیم
    with pytest.raises(AuthError):
        auth_service.refresh(first.refresh_token)

    rows = db_session.query(RefreshToken).filter_by(user_id=user.id).all()
    assert all(r.revoked_at is not None for r in rows), "کل زنجیره باید باطل شده باشد"

    # حتی توکن سوم (که هنوز منقضی نشده بود) دیگر کار نمی‌کند
    with pytest.raises(AuthError):
        auth_service.refresh(third.refresh_token)


def test_logout_revokes_token(auth_service, user, db_session):
    pair = auth_service.issue_token_pair(user)
    auth_service.logout(pair.refresh_token)

    with pytest.raises(AuthError):
        auth_service.refresh(pair.refresh_token)


def test_get_user_from_access_token(auth_service, user):
    pair = auth_service.issue_token_pair(user)
    fetched = auth_service.get_user_from_access_token(pair.access_token)
    assert fetched.id == user.id


def test_get_user_from_refresh_token_rejected(auth_service, user):
    pair = auth_service.issue_token_pair(user)
    with pytest.raises(AuthError):
        auth_service.get_user_from_access_token(pair.refresh_token)
