import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  ثبت مدل‌ها روی Base.metadata
from app.api.deps import get_db, get_email_provider, get_redis, get_sms_provider
from app.db.session import Base
from app.main import app as fastapi_app
from app.providers.email.console import ConsoleEmailProvider
from app.providers.sms.console import ConsoleSmsProvider


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
