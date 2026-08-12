from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import (
    get_client_ip,
    get_current_user,
    get_db,
    get_email_provider,
    get_redis,
    get_sms_provider,
)
from app.core.config import get_settings
from app.core.rate_limit_middleware import limiter
from app.core.validators import InvalidEmail, InvalidPhoneNumber
from app.models.otp_challenge import OTPPurpose
from app.models.user import User
from app.providers.email.base import EmailProvider
from app.providers.sms.base import SmsProvider
from app.schemas.auth import (
    AccessTokenOut,
    OTPRequestIn,
    OTPRequestOut,
    OTPResendIn,
    OTPVerifyIn,
    OTPVerifyOut,
    UserOut,
)
from app.services.auth_service import AuthError, AuthService
from app.services.otp_service import OTPRequestThrottled, OTPService, OTPVerificationFailed

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _otp_service(
    db: Session,
    redis_client: Redis,
    sms_provider: SmsProvider,
    email_provider: EmailProvider,
) -> OTPService:
    return OTPService(db, redis_client, sms_provider, email_provider)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/",
    )


@router.post("/otp/request", response_model=OTPRequestOut)
@limiter.exempt  # محدودیت اختصاصی OTP خودش را دارد؛ دوبار محدود نمی‌شود
def request_otp(
    body: OTPRequestIn,
    request: Request,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    sms_provider: SmsProvider = Depends(get_sms_provider),
    email_provider: EmailProvider = Depends(get_email_provider),
):
    settings = get_settings()
    service = _otp_service(db, redis_client, sms_provider, email_provider)
    try:
        challenge = service.request_otp(
            destination=body.destination,
            channel=body.channel,
            purpose=body.purpose,
            request_ip=get_client_ip(request),
        )
    except (InvalidPhoneNumber, InvalidEmail) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    except OTPRequestThrottled as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, str(exc), headers={"Retry-After": str(exc.retry_after)}
        ) from exc

    return OTPRequestOut(
        challenge_id=challenge.id,
        expires_in=settings.otp_expiration_seconds,
        retry_after=settings.otp_resend_cooldown_seconds,
    )


@router.post("/otp/resend", response_model=OTPRequestOut)
@limiter.exempt
def resend_otp(
    request: Request,
    body: OTPResendIn,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    sms_provider: SmsProvider = Depends(get_sms_provider),
    email_provider: EmailProvider = Depends(get_email_provider),
):
    settings = get_settings()
    service = _otp_service(db, redis_client, sms_provider, email_provider)
    try:
        challenge = service.resend_otp(body.challenge_id)
    except OTPRequestThrottled as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, str(exc), headers={"Retry-After": str(exc.retry_after)}
        ) from exc
    except OTPVerificationFailed as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return OTPRequestOut(
        challenge_id=challenge.id,
        expires_in=settings.otp_expiration_seconds,
        retry_after=settings.otp_resend_cooldown_seconds,
    )


@router.post("/otp/verify", response_model=OTPVerifyOut)
@limiter.exempt
def verify_otp(
    body: OTPVerifyIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    sms_provider: SmsProvider = Depends(get_sms_provider),
    email_provider: EmailProvider = Depends(get_email_provider),
):
    service = _otp_service(db, redis_client, sms_provider, email_provider)
    try:
        challenge = service.verify_otp(body.challenge_id, body.otp)
    except OTPVerificationFailed:
        return OTPVerifyOut(success=False, verified=False, message="کد وارد‌شده نامعتبر یا منقضی‌شده است")

    if challenge.purpose != OTPPurpose.LOGIN:
        return OTPVerifyOut(success=True, verified=True)

    auth_service = AuthService(db)
    user = auth_service.get_or_create_user(challenge.destination, challenge.channel.value)
    tokens = auth_service.issue_token_pair(
        user, user_agent=request.headers.get("user-agent"), ip=get_client_ip(request)
    )
    _set_refresh_cookie(response, tokens.refresh_token)

    return OTPVerifyOut(
        success=True, verified=True, access_token=tokens.access_token, token_type="bearer"
    )


@router.post("/refresh", response_model=AccessTokenOut)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_cookie = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_cookie:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "نشست یافت نشد؛ وارد شوید")

    auth_service = AuthService(db)
    try:
        tokens = auth_service.refresh(
            refresh_cookie, user_agent=request.headers.get("user-agent"), ip=get_client_ip(request)
        )
    except AuthError as exc:
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    _set_refresh_cookie(response, tokens.refresh_token)
    return AccessTokenOut(access_token=tokens.access_token)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_cookie = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_cookie:
        AuthService(db).logout(refresh_cookie)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return {"success": True}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
