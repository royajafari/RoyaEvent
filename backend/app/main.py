from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.auth import router as auth_router
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # در dev/MVP جدول‌ها مستقیم از روی مدل‌ها ساخته می‌شوند؛ برای production
    # از Alembic (backend/app/db/migrations) استفاده کنید.
    import app.models  # noqa: F401  ensures models are registered on Base.metadata

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}
