from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis as _get_redis
from app.db.session import get_db as _get_db
from app.models.user import User
from app.providers.email.base import EmailProvider
from app.providers.email.factory import get_email_provider as _get_email_provider
from app.providers.sms.base import SmsProvider
from app.providers.sms.factory import get_sms_provider as _get_sms_provider
from app.services.auth_service import AuthError, AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_redis() -> Redis:
    return _get_redis()


def get_sms_provider() -> SmsProvider:
    return _get_sms_provider()


def get_email_provider() -> EmailProvider:
    return _get_email_provider()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "احراز هویت لازم است")
    try:
        return AuthService(db).get_user_from_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "این عملیات فقط برای ادمین مجاز است")
    return current_user
