import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  ثبت مدل‌ها روی Base.metadata
from app.api.deps import get_db, get_email_provider, get_redis, get_sms_provider
from app.core.rate_limit_middleware import limiter
from app.db.session import Base
from app.main import app as fastapi_app
from app.models.category import Category
from app.models.user import User
from app.providers.email.console import ConsoleEmailProvider
from app.providers.sms.console import ConsoleSmsProvider


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """limiter عمومی (slowapi) در حافظه‌ی همان پردازه است؛ بدون ریست، تست‌های
    پیاپی که یک endpoint محدودشده را چند بار صدا می‌زنند به هم نشت می‌کنند."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _mock_search_indexing(monkeypatch):
    """sync_event_index واقعی مدل embedding سنگین (sentence-transformers) رو
    لود و اجرا می‌کنه — بدون این mock، هر تستی که رویدادی publish/cancel/
    update کنه (یعنی اکثر تست‌های events/orders/social/instructors) کند
    می‌شد یا حتی fail می‌کرد (بار اول نیاز به دانلود مدل از HuggingFace
    داره). تست‌های اختصاصی جستجو (test_search_api.py) خودشون این mock رو
    override می‌کنن تا رفتار واقعی ایندکس رو با embedding قلابی بررسی کنن."""
    import app.services.event_service as event_service_module

    monkeypatch.setattr(event_service_module, "sync_event_index", lambda event: None)


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    client.flushall()


@pytest.fixture()
def sms_provider():
    return ConsoleSmsProvider()


@pytest.fixture()
def email_provider():
    return ConsoleEmailProvider()


@pytest.fixture()
def otp_service(db_session, fake_redis, sms_provider, email_provider):
    from app.services.otp_service import OTPService

    return OTPService(db_session, fake_redis, sms_provider, email_provider)


@pytest.fixture()
def auth_service(db_session):
    from app.services.auth_service import AuthService

    return AuthService(db_session)


@pytest.fixture()
def client(db_session, fake_redis, sms_provider, email_provider):
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    fastapi_app.dependency_overrides[get_redis] = lambda: fake_redis
    fastapi_app.dependency_overrides[get_sms_provider] = lambda: sms_provider
    fastapi_app.dependency_overrides[get_email_provider] = lambda: email_provider

    # بدون `with` تا رویداد lifespan (که به دیتابیس واقعی وصل می‌شود) اجرا نشود
    test_client = TestClient(fastapi_app)
    yield test_client

    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def organizer(db_session):
    user = User(phone="09121234567", full_name="برگزارکننده‌ی تست")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(auth_service, organizer):
    tokens = auth_service.issue_token_pair(organizer)
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture()
def leaf_category(db_session):
    parent = Category(name="فناوری اطلاعات", slug="technology", parent_id=None)
    db_session.add(parent)
    db_session.flush()
    child = Category(name="هوش مصنوعی", slug="ai", parent_id=parent.id)
    db_session.add(child)
    db_session.commit()
    db_session.refresh(child)
    return child


@pytest.fixture()
def admin_user(db_session):
    from app.models.user import UserRole

    user = User(phone="09399999999", full_name="ادمین تست", role=UserRole.ADMIN)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_auth_headers(auth_service, admin_user):
    tokens = auth_service.issue_token_pair(admin_user)
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture()
def buyer(db_session):
    user = User(phone="09351234567", full_name="خریدار تست")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def buyer_auth_headers(auth_service, buyer):
    tokens = auth_service.issue_token_pair(buyer)
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture()
def published_event(db_session, leaf_category, organizer):
    from datetime import datetime, timedelta

    from app.schemas.event import EventCreateIn, EventSessionIn
    from app.services import event_service

    data = EventCreateIn(
        title="کارگاه تست",
        description="توضیحات کارگاه تست",
        category_id=leaf_category.id,
        format="online",
        online_platform_name="SkyRoom",
        visibility="public",
        sessions=[EventSessionIn(starts_at=datetime.now() + timedelta(days=10), duration_minutes=60)],
    )
    event = event_service.create_event(db_session, organizer.id, data)
    return event_service.publish_event(db_session, event)


@pytest.fixture()
def free_ticket_type(db_session, published_event):
    from app.schemas.ticket import TicketTypeIn
    from app.services import ticket_service

    data = TicketTypeIn(name="بلیط رایگان", pricing_model="free")
    return ticket_service.create_ticket_type(db_session, published_event, data)


@pytest.fixture()
def paid_ticket_type(db_session, published_event):
    from app.schemas.ticket import TicketTypeIn
    from app.services import ticket_service

    data = TicketTypeIn(name="بلیط ویژه", pricing_model="paid", price=150000)
    return ticket_service.create_ticket_type(db_session, published_event, data)
