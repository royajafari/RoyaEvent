import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.routers.admin import router as admin_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.events import router as events_router
from app.api.v1.routers.home import router as home_router
from app.api.v1.routers.instructors import router as instructors_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.organizer import router as organizer_router
from app.api.v1.routers.organizers import router as organizers_router
from app.api.v1.routers.ratings import router as ratings_router
from app.api.v1.routers.search import router as search_router
from app.api.v1.routers.social import router as social_router
from app.api.v1.routers.tickets import router as tickets_router
from app.api.v1.routers.track import router as track_router
from app.core.config import get_settings
from app.core.logging_config import setup_json_logging
from app.core.rate_limit_middleware import limiter
from app.db.session import Base, engine

settings = get_settings()

# بدون این، لاگرهای خودمون (مثل ConsoleSmsProvider که OTP توسعه رو نشون
# می‌ده) به‌خاطر سطح پیش‌فرض WARNING روی root logger، اصلاً چاپ نمی‌شن.
# از فاز ۹، خروجی JSON ساختاریافته‌ست (نه متن‌ساده) تا Promtail/Loki بتونن
# فیلدها (سطح/logger/پیام) رو جدا پارس کنن.
setup_json_logging(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # در dev/MVP جدول‌ها مستقیم از روی مدل‌ها ساخته می‌شوند؛ برای production
    # از Alembic (backend/app/db/migrations) استفاده کنید.
    import app.models  # noqa: F401  ensures models are registered on Base.metadata

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(events_router, prefix=settings.api_v1_prefix)
app.include_router(tickets_router, prefix=settings.api_v1_prefix)
app.include_router(orders_router, prefix=settings.api_v1_prefix)
app.include_router(social_router, prefix=settings.api_v1_prefix)
app.include_router(organizer_router, prefix=settings.api_v1_prefix)
app.include_router(organizers_router, prefix=settings.api_v1_prefix)
app.include_router(instructors_router, prefix=settings.api_v1_prefix)
app.include_router(search_router, prefix=settings.api_v1_prefix)
app.include_router(home_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(ratings_router, prefix=settings.api_v1_prefix)
app.include_router(track_router, prefix=settings.api_v1_prefix)

if settings.prometheus_enabled:
    from app.core import metrics as _metrics

    @app.middleware("http")
    async def _prometheus_http_metrics(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        # بعد از call_next، روتینگ استارلت انجام شده و scope["route"] ست
        # می‌شه — از path template (مثل /events/{slug}) استفاده می‌کنیم نه
        # request.url.path خام، وگرنه هر مقدار متفاوت پارامتر یک سری کاردینالیتی
        # جدا در Prometheus می‌سازه (مثلاً یک سری به‌ازای هر slug رویداد).
        route = request.scope.get("route")
        path = route.path if route is not None else request.url.path
        _metrics.http_requests_total.labels(
            method=request.method, path=path, status=response.status_code
        ).inc()
        _metrics.http_request_duration_seconds.labels(method=request.method, path=path).observe(
            duration
        )
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics_endpoint():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}
