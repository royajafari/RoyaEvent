from fastapi.security import HTTPAuthorizationCredentials

from app.api import deps


def test_get_current_user_optional_returns_none_without_credentials(db_session):
    assert deps.get_current_user_optional(credentials=None, db=db_session) is None


def test_get_current_user_optional_returns_none_on_invalid_token(db_session):
    """برخلاف get_current_user (که ۴۰۱ می‌ده)، نسخه‌ی optional فقط None
    برمی‌گردونه تا endpointهای عمومی (مثل صفحه‌ی مدرس/برگزارکننده) با یک
    توکن نامعتبر/منقضی‌شده به‌جای ۴۰۱ خام، ساده رفتار «کاربر لاگین نکرده»
    رو بگیرن."""
    bogus_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage-token")
    assert deps.get_current_user_optional(credentials=bogus_credentials, db=db_session) is None
