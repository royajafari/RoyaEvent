"""صدور/چرخش JWT — بخش ۷ پلن معماری: access کوتاه + refresh چرخشی با
تشخیص استفاده‌ی مجدد (reuse detection) از طریق زنجیره‌ی replaced_by.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token_jwt,
    decode_token,
    hash_refresh_token,
    new_jti,
)
from app.models.base import utcnow
from app.models.otp_challenge import OTPChannel
from app.models.refresh_token import RefreshToken
from app.models.user import User


class AuthError(Exception):
    pass


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token


class AuthService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()

    def get_or_create_user(self, destination: str, channel: str) -> User:
        field = "phone" if channel == OTPChannel.SMS.value else "email"
        user = self.db.query(User).filter_by(**{field: destination}).first()
        if user is not None:
            return user

        user = User(**{field: destination})
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def issue_token_pair(
        self, user: User, user_agent: str | None = None, ip: str | None = None
    ) -> TokenPair:
        jti = new_jti()
        refresh_jwt = create_refresh_token_jwt(user.id, jti)
        now = utcnow()

        token_row = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_jwt),
            jti=jti,
            expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip=ip,
        )
        self.db.add(token_row)

        user.last_login_at = now
        self.db.commit()

        access_token = create_access_token(user.id)
        return TokenPair(access_token=access_token, refresh_token=refresh_jwt)

    def refresh(
        self, refresh_token_plain: str, user_agent: str | None = None, ip: str | None = None
    ) -> TokenPair:
        try:
            decode_token(refresh_token_plain)
        except ValueError as exc:
            raise AuthError("توکن نامعتبر یا منقضی‌شده است") from exc

        token_hash = hash_refresh_token(refresh_token_plain)
        row = self.db.query(RefreshToken).filter_by(token_hash=token_hash).first()
        if row is None:
            raise AuthError("توکن نامعتبر است")

        if row.revoked_at is not None:
            # استفاده‌ی مجدد از توکن باطل‌شده = تشخیص سرقت → کل زنجیره باطل می‌شود
            self._revoke_chain_forward(row)
            raise AuthError("نشست شما به دلایل امنیتی باطل شد؛ دوباره وارد شوید")

        now = utcnow()
        if now > row.expires_at:
            raise AuthError("نشست منقضی شده است؛ دوباره وارد شوید")

        user = self.db.get(User, row.user_id)
        new_pair = self.issue_token_pair(user, user_agent=user_agent, ip=ip)

        new_row = (
            self.db.query(RefreshToken)
            .filter_by(token_hash=hash_refresh_token(new_pair.refresh_token))
            .first()
        )
        row.revoked_at = now
        row.replaced_by = new_row.id
        self.db.commit()

        return new_pair

    def logout(self, refresh_token_plain: str) -> None:
        token_hash = hash_refresh_token(refresh_token_plain)
        row = self.db.query(RefreshToken).filter_by(token_hash=token_hash).first()
        if row is not None and row.revoked_at is None:
            row.revoked_at = utcnow()
            self.db.commit()

    def _revoke_chain_forward(self, start: RefreshToken) -> None:
        now = utcnow()
        current: RefreshToken | None = start
        while current is not None:
            if current.revoked_at is None:
                current.revoked_at = now
            current = self.db.get(RefreshToken, current.replaced_by) if current.replaced_by else None
        self.db.commit()

    def get_user_from_access_token(self, access_token: str) -> User:
        try:
            payload = decode_token(access_token)
        except ValueError as exc:
            raise AuthError("توکن نامعتبر یا منقضی‌شده است") from exc

        if payload.get("type") != "access":
            raise AuthError("نوع توکن نامعتبر است")

        user = self.db.get(User, int(payload["sub"]))
        if user is None:
            raise AuthError("کاربر یافت نشد")
        return user
