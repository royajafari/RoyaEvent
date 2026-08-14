from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RoyaEvent API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: list[str] = ["http://localhost:3000"]

    # دیتابیس
    sqlite_path: str = "./roya_event.db"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "royaevent_analytics"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "royaevent"
    minio_secret_key: str = "royaevent_secret"
    minio_bucket: str = "royaevent-media"
    minio_secure: bool = False

    # JWT — بخش ۷ پلن: access کوتاه، refresh چرخشی
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 1

    # OTP — طبق event_otp_email_sms_plan_fa.md، بخش ۲۰
    otp_hash_secret: str = "CHANGE_ME_OTP_SECRET"
    otp_length: int = 6
    otp_expiration_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60
    otp_max_requests_per_minute: int = 1
    otp_max_requests_per_hour: int = 5
    otp_max_requests_per_day: int = 20
    otp_ip_max_requests_per_10_minutes: int = 10

    # Provider ها
    sms_provider: str = "ippanel"
    ippanel_api_key: str = ""
    ippanel_sender_number: str = ""
    kavenegar_api_key: str = ""
    kavenegar_sender: str = ""

    email_provider: str = "brevo"
    brevo_api_key: str = ""
    brevo_sender_email: str = "no-reply@royaevent.ir"
    brevo_sender_name: str = "رویا ایونت"
    resend_api_key: str = ""

    # Vector search
    chroma_persist_dir: str = "./chroma_data"

    # مانیتورینگ
    prometheus_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
