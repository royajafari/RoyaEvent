# فاز ۹ — استک مانیتورینگ

وضعیت: ✅ کامل (بک‌اند + زیرساخت docker-compose)، تست‌شده، لینت تمیز، `/health` و `/metrics` زنده تأیید شد.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن + مدرس/آواتار/تکمیل پروفایل اجباری. فاز ۴: جستجوی معنایی (ChromaDB) + صفحه‌ی اصلی. فاز ۵: پنل ادمین. فاز ۶: صف اعلان‌ها + worker زمان‌بند + soft-delete رویداد. فاز ۷: امتیاز/نظر ۴محوره. فاز ۸: بیکن آنالیتیکس (Mongo) + رول‌آپ شبانه‌ی KPI (SQLite) + گزارش ادمین. جمعاً ۳۰۸ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec8.md`](spec8.md).

## هدف

بخش ۱ و فاز ۹ نقشه‌ی راه (`docs/architecture.md`): instrumentation Prometheus روی بک‌اند (`/metrics`)، لاگ ساختاریافته JSON برای Loki/Promtail، و داشبورد Grafana آماده که سلامت API، قیف OTP، حجم سفارش، و backlog صف اعلان رو نشون بده. `infra/docker-compose.yml` از قبل (فاز ۰) کانتینرهای Loki/Prometheus/Grafana رو داشت اما بدون هیچ داده‌ی واقعی‌ای که scrape کنه — این فاز اون سیم‌کشی مصرف‌کننده رو کامل کرد.

## چیزی که ساخته شد

### بک‌اند

- **`app/core/metrics.py`** (جدید): متریک‌های Prometheus.
  - HTTP عمومی: `royaevent_http_requests_total{method,path,status}` (Counter) و `royaevent_http_request_duration_seconds{method,path}` (Histogram) — با `path` = **path template** (مثل `/api/v1/events/{slug}`)، نه URL خام، تا کاردینالیتی متریک به ازای هر مقدار پارامتر منفجر نشه.
  - کسب‌وکاری: `royaevent_otp_requested_total`/`royaevent_otp_verified_total`/`royaevent_otp_failed_total` (هر سه با لیبل `channel`)، `royaevent_orders_completed_total`، و `royaevent_notification_outbox_pending` (Gauge با `set_function` — عدد زنده‌ی ردیف‌های `PENDING` در `notification_outbox`، فقط موقع scrape شدن از DB خونده می‌شه، نه یک job جدا).
- **middleware ساده در `app/main.py`** (نه یک کتابخونه‌ی شخص ثالث — نگاه کن به بخش «نکات/دام‌های این فاز» برای چرا): زمان هر درخواست رو اندازه می‌گیره، `route = request.scope.get("route")` رو بعد از `call_next` می‌خونه تا path template رو به‌جای URL خام بگیره، و `royaevent_http_requests_total`/`royaevent_http_request_duration_seconds` رو پر می‌کنه. `GET /metrics` (خارج از `api_v1_prefix`، `include_in_schema=False`) خروجی `generate_latest()` رو با `content-type` درست برمی‌گردونه. همه‌ی این‌ها پشت `if settings.prometheus_enabled:` (فلگ از قبل در `config.py` بود، این فاز اولین مصرف‌کننده‌شه).
- **متریک‌ها تو سرویس‌ها وایر شدن**: `otp_service.py` (`request_otp` → `otp_requested_total.inc()`؛ هر ۴ مسیر شکست `verify_otp` + مسیر موفق → `otp_failed_total`/`otp_verified_total`)، `order_service.py` (`complete_order` → `orders_completed_total.inc()`).
- **`app/core/logging_config.py`** (جدید): `JsonFormatter` (stdlib `logging.Formatter`، بدون وابستگی جدید مثل `python-json-logger`) + `setup_json_logging()`. جایگزین `logging.basicConfig(format="%(asctime)s %(name)s %(message)s")` قبلی در `main.py` و `scheduler.py` — خروجی حالا هر خط یک JSON با فیلدهای `ts/level/logger/message(/exception)` است تا Promtail بتونه فیلد به فیلد پارس کنه.
- **زیرساخت مانیتورینگ (`infra/`)**:
  - `infra/promtail/promtail-config.yml` + سرویس `promtail` جدید در `infra/docker-compose.yml`.
  - `infra/grafana/provisioning/dashboards/dashboards.yml` (file provider) + `royaevent-overview.json` — ۷ پنل: نرخ درخواست HTTP، تأخیر p95، نرخ خطای ۵xx، backlog صف اعلان، قیف OTP (درخواست/تأیید/شکست بر ساعت)، حجم سفارش تکمیل‌شده، و یک پنل لاگ خطا/هشدار از Loki.
  - `infra/grafana/provisioning/datasources/datasources.yml`: به هر دو دیتاسورس (`Prometheus`/`Loki`) یک `uid` صریح اضافه شد (`royaevent-prometheus`/`royaevent-loki`) تا داشبورد بتونه بدون متغیر templating مستقیم بهشون رفرنس بده.
- **۴ تست جدید** (`tests/integration/test_metrics.py`): `/metrics` واقعاً ۲۰۰ و شامل متریک‌های سفارشی برمی‌گردونه؛ درخواست/تأیید OTP شمارنده‌ی مربوطه رو افزایش می‌ده؛ تأیید ناموفق OTP شمارنده‌ی شکست رو افزایش می‌ده؛ تکمیل سفارش شمارنده‌ی سفارش رو افزایش می‌ده. جمعاً **۳۱۲ تست پاس**.

### خارج از دامنه‌ی این فاز (عمداً)

- `infra/docker-compose.prod.yml` هنوز هیچ سرویس مانیتورینگی نداره — تصمیم گرفته شد این تصمیم (مانیتورینگ production جدا/مشترک با dev، secrets Grafana admin، و غیره) به فاز ۱۱ (دیپلوی VPS) موکول بشه، نه این‌جا.

## نکات/دام‌های این فاز

- **`prometheus-fastapi-instrumentator==7.1.0` با نسخه‌ی جدید Starlette این پروژه (`0.52.1`) اصلاً کار نمی‌کنه** — `AttributeError: '_IncludedRouter' object has no attribute 'path'` موقع اولین درخواست (نه موقع import/startup، پس تست‌ها بلافاصله لو دادنش). اون کتابخونه برای ساختار داخلی قدیمی‌تر Router استارلت نوشته شده و به‌روز نشده. راه‌حل: کنارش گذاشتیم، به‌جاش با `prometheus_client` مستقیم (که خودش وابستگی همون کتابخونه بود و از قبل نصب شده بود) یک middleware ساده‌ی ~۱۵ خطی نوشتیم — کنترل کامل، بدون تکیه به API داخلی شکننده‌ی یک کتابخونه‌ی شخص ثالث. اگه در آینده دوباره وسوسه شدی از یک "instrumentator" آماده استفاده کنی، اول با آخرین نسخه‌ی FastAPI/Starlette این پروژه (که همیشه خیلی جلوعه) تست کن.
- **`import app.core.metrics` داخل `main.py` اسم محلی `app` (نمونه‌ی FastAPI) رو با ماژول بسته‌ی `app` جایگزین می‌کنه** — یک dotted import مثل `import app.core.metrics` همیشه اسم *ریشه*ی مسیر (`app`) رو در namespace جاری bind می‌کنه، نه فقط زیرماژول نهایی. چون `main.py` خودش از قبل یک متغیر سطح‌ماژول به اسم `app = FastAPI(...)` داره، این import بی‌صدا جایگزینش می‌کنه و خطای گیج‌کننده‌ای می‌ده (`'module' object has no attribute 'add_middleware'`) که ربطی به prometheus نداره. راه‌حل: همیشه `from app.core import metrics` (یا با اسم مستعار) بنویس وقتی داخل ماژولی هستی که خودش یه متغیر به اسم `app` داره.
- **متریک `path` باید از `route.path` (template) باشه، نه `request.url.path` خام** — وگرنه هر مقدار متفاوت پارامتر مسیر (هر `slug` رویداد، هر `id` کاربر) یک سری متریک کاملاً جدا در Prometheus می‌سازه (کاردینالیتی نامحدود، مشکل شناخته‌شده‌ی معمول instrumentation نادرست). `request.scope["route"]` فقط *بعد از* `await call_next(request)` ست می‌شه (چون routing استارلت عمیق‌تر از این middleware اتفاق می‌افته)، نه قبلش.
- **backlog صف اعلان (Gauge با `set_function`) بیرون از request scope صدا زده می‌شه** — پس نمی‌تونه از `get_db` تزریق‌شده استفاده کنه، مستقیم یه `SessionLocal()` واقعی می‌سازه. در محیط تست که `client` fixture عمداً lifespan (و `Base.metadata.create_all`) رو اجرا نمی‌کنه، این یعنی جدول `notification_outbox` روی DB واقعی ممکنه وجود نداشته باشه؛ callback با `try/except` این حالت رو می‌بلعه و `0.0` برمی‌گردونه به‌جای این‌که کل `/metrics` رو بترکونه — چون شکست یک متریک جانبی نباید کل endpoint مانیتورینگ رو خراب کنه.
- **بک‌اند در dev مستقیم روی هاست اجرا می‌شه (uvicorn/scheduler)، نه در یک کانتینر** — پس روش معمول Promtail (docker service discovery روی لاگ کانتینرها) اصلاً لاگ اپلیکیشن رو نمی‌بینه (فقط لاگ mongo/redis/minio که بی‌فایده‌ست). به‌جاش Promtail یک دایرکتوری مشترک استاتیک (`infra/logs/*.log`) رو می‌خونه که هم dev هاست‌محور هم (در آینده، فاز ۱۱) کانتینرهای production می‌تونن بهش بنویسن. فعلاً فعال‌سازی این مسیر برای dev دستیه (ریدایرکت خروجی uvicorn/scheduler به یک فایل زیر `infra/logs/`)، چون تغییر دستور استاندارد `uvicorn --reload` که همه‌جای مستندات ازش استفاده می‌شه ضروری نیست.

## راستی‌آزمایی

- `ruff check .` تمیز، `pytest -q` → **۳۱۲ تست پاس**.
- `TestClient` با lifespan واقعی: `GET /health` → ۲۰۰، `GET /metrics` → ۲۰۰ با `content-type: text/plain; version=1.0.0; charset=utf-8` و شامل متریک‌های سفارشی.
- `infra/grafana/provisioning/dashboards/royaevent-overview.json` با `json.load` اعتبارسنجی شد (سینتکس معتبر).

## Commitهای مرتبط

(در ادامه‌ی همین نشست کامیت می‌شه — نگاه کن به تاریخچه‌ی گیت برای هش دقیق.)
