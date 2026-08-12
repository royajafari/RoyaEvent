# CLAUDE.md — RoyaEvent

راهنمای جهت‌یابی سریع برای Claude Code در این ریپو. برای معماری کامل/تصمیمات ریز به [`docs/architecture.md`](docs/architecture.md) مراجعه کن؛ این فایل خلاصه‌ی وضعیت فعلی + قراردادها + نکات عملیاتیه که یک نشست تازه بلافاصله بهش نیاز داره.

## پروژه چیست

**RoyaEvent** — پلتفرم فارسی/RTL مدیریت رویداد و وبینار (شبیه eseminar.tv و evand.com، تحلیل رقبا در `data/`). صاحب پروژه: کاربر فارسی‌زبان، ارتباط همیشه به فارسی. کد/کامنت/پیام‌های کاربر همه فارسی‌اند مگر اسم فنی (متغیر، تابع) که انگلیسی می‌مونه.

مالک مخزن گیت‌هاب: `royajafari` (public) — https://github.com/royajafari/RoyaEvent

## استک فنی (تصمیم قطعی، تغییر نده مگر کاربر بخواد)

| لایه | فناوری |
|---|---|
| فرانت‌اند | Next.js 16 (App Router) + shadcn/ui (بر پایه‌ی Base UI، نه Radix) + Tailwind v4، RTL/فارسی |
| بک‌اند | FastAPI (Python 3.12) |
| DB اصلی | SQLite (WAL mode)، از طریق SQLAlchemy 2.0 + Alembic |
| آنالیتیکس رفتاری | MongoDB (فاز ۸، هنوز کدی نیست) |
| کش/Rate-limit | Redis |
| فایل/بنر | MinIO (S3-compatible) |
| جستجوی محتوایی | ChromaDB embedded (فاز ۴، هنوز نیست) |
| احراز هویت | OTP-only (بدون پسورد) + JWT (access کوتاه + refresh چرخشی) |
| SMS | IPPanel (اصلی) / Kavenegar (جایگزین) |
| Email | Brevo (اصلی) / Resend (جایگزین) |
| مانیتورینگ | Loki + Prometheus + Grafana (فاز ۹، فقط docker-compose آماده‌ست) |
| فونت | Kalameh (محلی، `frontend/src/fonts/kalameh/*.woff2`، فایل تجاری — نکته‌ی لایسنس پایین صفحه) |

## ساختار پوشه‌ها

```
RoyaEvent/
  backend/app/
    api/v1/routers/   # auth.py, events.py
    api/deps.py        # get_db, get_current_user, get_redis, get_sms/email_provider, get_client_ip
    core/               # config, security (JWT+OTP hash), rate_limit (OTP), rate_limit_middleware (عمومی/slowapi)
                        # redis_client, storage (MinIO), slug, validators
    db/                 # session.py (engine/Base/get_db)، migrations/ (Alembic)، seed_categories.py
    models/             # User, OTPChallenge, RefreshToken, Category, Tag, Instructor, Event, EventSession
    providers/sms|email/ # base + console(dev) + ippanel/kavenegar/brevo/resend
    schemas/            # auth.py, event.py (Pydantic)
    services/           # otp_service, auth_service, event_service, image_service
  backend/tests/unit|integration/   # pytest، fakeredis، بدون نیاز به Redis واقعی
  frontend/src/
    app/                # (auth)/login/page.tsx، page.tsx (خانه)
    components/ui/      # shadcn primitives
    lib/api-client.ts    # fetch wrapper، credentials:include
    store/auth-store.ts  # Zustand، access token فقط در حافظه
    fonts/kalameh.ts
  infra/docker-compose.yml   # redis, mongo, minio, loki, prometheus, grafana
  data/eseminar.tv/, data/evand.com/   # تحلیل رقبا
  docs/architecture.md        # پلن کامل معماری (مرجع اصلی)
  docs/event_otp_email_sms_plan_fa.md  # سند اولیه‌ی OTP (کاربر داده، مرجع دقیق مکانیزم OTP)
```

## وضعیت فعلی — فاز به فاز

نقشه‌ی راه کامل در `docs/architecture.md` بخش ۱۴. خلاصه:

- **فاز ۰ (Scaffolding)** ✅ کامل و commit‌شده.
- **فاز ۱ (Auth/OTP)** ✅ کامل، تست‌شده، commit‌شده، push‌شده.
- **فاز ۲ (Event CRUD + دسته‌بندی/تگ/جلسه + آپلود بنر امن)** ✅ **بک‌اند کامل، تست‌شده، لینت تمیز — هنوز commit/push نشده.** فرانت‌اند فاز ۲ هنوز شروع نشده. جزئیات زیر.
- فازهای ۳ تا ۱۱: هنوز شروع نشده (تیکتینگ، جستجو، ادمین، اعلان‌ها، امتیازدهی، آنالیتیکس، مانیتورینگ، تست/RTL نهایی، دیپلوی).

**بک‌اند در مجموع الان ۱۰۱ تست دارد (unit + integration)، همه پاس، `ruff check .` تمیز.**

### فاز ۲ — بک‌اند کامل و wired؛ فرانت‌اند باقی مانده

**بک‌اند (کامل، تست‌شده، uncommitted):**
- مدل‌ها: `Category` (دوسطحی، self-FK)، `Tag`، `Instructor`، `Event`، `EventSession`، جدول‌های M:N `event_tags`/`event_instructors`
- Alembic migration `567deeea1757` روی پایه‌ی `07c06a1dc198` — `alembic upgrade head` تست شده، جدول‌ها verify شدند (`categories, tags, events, instructors, event_instructors, event_sessions, event_tags` + جدول‌های فاز ۱)
- `app/db/seed_categories.py` — ۱۰ دسته‌ی والد × ۳-۵ زیردسته (اجرا: `python -m app.db.seed_categories`) — **هنوز در محیط dev واقعی اجرا نشده**، فقط در تست از طریق فیکسچر `leaf_category` استفاده می‌شه
- `app/services/image_service.py` — `validate_and_reencode_image()`: magic-byte check با Pillow، رد SVG، محدودیت ۵MB/۴۰۰۰px، همیشه خروجی JPEG تازه (حتی PNG/WebP ورودی) با flatten روی پس‌زمینه‌ی سفید — طبق بخش ۱۶ پلن. ۹ تست (شامل تست این‌که payload الحاقی به انتهای فایل در خروجی نیست)
- `app/core/storage.py` — کلاینت MinIO + `ensure_bucket_ready()` (public-read) + `upload_banner_image()` — **در تست mock می‌شه** (`monkeypatch.setattr(events_module, "upload_banner_image", ...)`)، نیازی به MinIO واقعی برای تست نیست
- `app/core/slug.py` — `slugify_ascii()` + `generate_numeric_code()` (کد رویداد ۶رقمی)
- `app/services/event_service.py` — create/update/publish/cancel event، replace_sessions، تولید slug/event_code یکتا، اعتبارسنجی این‌که category باید زیردسته (برگ) باشه، get-or-create برای تگ‌ها
- `app/schemas/event.py` — Pydantic schemas کامل
- `app/api/v1/routers/events.py` — همه‌ی endpointها نوشته و **در `main.py` wire شده**:
  `GET/POST /events`, `GET /events/mine`, `GET /events/id/{id}` (فقط مالک، DRAFT رو هم می‌ده)، `GET /events/code/{code}`, `GET /events/private/{token}`, `GET /events/{slug}` (فقط PUBLISHED)، `GET /events/{id}/related`, `PATCH/DELETE /events/{id}`, `PUT /events/{id}/sessions`, `POST /events/{id}/publish`, `POST /events/{id}/banner`, `GET /events/categories`
- `app/core/rate_limit_middleware.py` — Limiter عمومی slowapi (کلید = user_id اگه لاگین باشه وگرنه IP، سقف پیش‌فرض ۱۲۰/دقیقه)؛ روی `create_event`/`update_event`/`replace_event_sessions` سقف ۲۰/دقیقه، `upload_event_banner` سقف ۱۰/دقیقه. سه endpoint اختصاصی OTP (`otp/request`, `otp/resend`, `otp/verify`) همگی `@limiter.exempt` دارن (محدودیت خودشون رو دارن، طبق بخش ۶ پلن).
- `app/main.py` — `events_router` include شده، `SlowAPIMiddleware`/`app.state.limiter`/exception-handler وصله.
- **رفع یک باگ امنیتی واقعی حین نوشتن تست:** اولین نسخه‌ی `get_event_by_slug`/`get_event_by_code`/`get_private_event` فقط `visibility` رو چک می‌کردن، نه `status` — یعنی رویداد **DRAFT منتشرنشده از طریق slug عمومی قابل مشاهده بود** (نشتی اطلاعات قبل از انتشار). اصلاح شد: هر سه endpoint حالا `status == PUBLISHED` رو هم الزامی می‌کنن. برای این‌که مالک هنوز بتونه پیش‌نویسش رو ببینه/ویرایش کنه، endpoint جدید `GET /events/id/{event_id}` (فقط مالک/ادمین، بدون محدودیت status) اضافه شد.

**تست‌ها:** `tests/unit/test_slug.py`, `test_image_service.py`, `test_event_service.py` + `tests/integration/test_events_api.py` (پوشش: auth، مالکیت/۴۰۳، DRAFT leak، publish idempotency، لیست عمومی در برابر `/mine`، رویداد خصوصی + توکن، آپلود بنر معتبر/نامعتبر/غیرمجاز، related events، دسته‌بندی‌ها). فیکسچرهای جدید در `conftest.py`: `organizer`, `auth_headers`, `leaf_category`, و یک `autouse` فیکسچر `_reset_rate_limiter` که `limiter.reset()` رو قبل/بعد هر تست صدا می‌زنه (وگرنه چون Limiter حافظه‌ی in-process داره، تست‌های پشت‌سرهم روی endpointهای rate-limit‌شده به هم نشت می‌کنن).

**هنوز نیاز به تکمیل:**
1. فرانت‌اند فاز ۲ اصلاً شروع نشده: نه فرم ایجاد رویداد برگزارکننده، نه صفحه‌ی عمومی جزئیات رویداد (`/events/[slug]`, باید SSR باشه طبق تصمیم کاربر برای SEO)، نه لیستینگ پایه.
2. `docs/architecture.md` بخش ۱۴ (نقشه‌ی راه) باید بعد از تکمیل کل فاز ۲ (شامل فرانت) به‌روزرسانی بشه (مثل الگوی فاز ۰/۱).
3. **نکته‌ی جزئی (غیرضروری، اختیاری):** حداکثر حجم بنر (۵ مگابایت) در دو جا جدا hardcode شده — `MAX_BANNER_UPLOAD_BYTES` در `events.py` و `MAX_UPLOAD_BYTES` در `image_service.py`. الان مقدارشون یکیه و مشکلی نمی‌سازه، ولی اگه یکی رو تغییر دادی حتماً اون یکی رو هم عوض کن؛ بهتره یه‌جا (مثلاً `core/config.py`) متمرکز بشه.
4. هنوز هیچ commit جدیدی برای فاز ۲ زده نشده — همه‌ی موارد بالا روی دیسک uncommitted هستن.

## قراردادهای API

- Base path: `/api/v1` (از `settings.api_v1_prefix`)
- Auth: `Authorization: Bearer <access_token>` برای access token (در حافظه‌ی فرانت، نه localStorage)؛ refresh token در کوکی httpOnly به اسم `refresh_token` (مسیر `/`)
- خطاها: `HTTPException` با پیام فارسی؛ برای OTP/Auth عمداً پیام‌های عمومی (بدون افشای این‌که کاربر/OTP وجود داره یا نه)
- همه‌ی مدل‌های زمانی در DB **naive UTC** هستن (نه timezone-aware) — SQLite مقایسه‌ی aware/naive رو با TypeError رد می‌کنه؛ همیشه از `app.models.base.utcnow()` استفاده کن، نه `datetime.now(timezone.utc)` مستقیم
- Provider abstraction: کد سرویس هرگز مستقیم IPPanel/Kavenegar/Brevo/Resend صدا نمی‌زنه؛ از `get_sms_provider()`/`get_email_provider()` (factory، بر اساس `.env`) رد می‌شه. بدون API key، خودکار می‌ره روی `ConsoleProvider` (فقط لاگ، برای dev/test)

## قراردادهای UI

- همه‌چیز RTL: `dir="rtl" lang="fa"` روی `<html>` (در `app/layout.tsx`)
- فونت: فقط Kalameh (`next/font/local`)، نه فونت دیگه
- کامپوننت‌های پایه از shadcn/ui؛ توجه: این نسخه‌ی shadcn روی **Base UI** ساخته شده نه Radix، پس `Button` پراپ `asChild` نداره — برای رندر به‌عنوان لینک از `buttonVariants({...})` روی `<Link>` مستقیم استفاده کن (نمونه در `frontend/src/app/page.tsx`)
- **ریسپانسیو الزامیه** (درخواست صریح کاربر) — mobile-first، از breakpointهای Tailwind استفاده کن، هر صفحه‌ی جدید رو حداقل در دو اندازه چک کن
- State سرور: TanStack Query (هنوز نصب/استفاده نشده، طرح فقط در پلنه) + Zustand برای state خالص کلاینت (فقط `auth-store.ts` فعلاً)

## محیط توسعه / اجرا

```bash
# سرویس‌های جانبی (Redis, Mongo, MinIO, Loki, Prometheus, Grafana)
docker compose -f infra/docker-compose.yml up -d

# بک‌اند
cd backend
.venv/Scripts/activate   # venv از قبل ساخته شده، فقط فعالش کن
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000/health

# فرانت‌اند
cd frontend
npm install
npm run dev   # http://localhost:3000
```

پورت‌ها: API=8000، Next=3000، Redis=6379، Mongo=27017، MinIO=9000/9001(console)، Loki=3100، Prometheus=9090، Grafana=3300 (نه 3000، تصادم با Next dev).

## نکات مهم/دام‌ها (از تجربه‌ی همین نشست)

1. **هرگز `import app.models` رو در `alembic/env.py` بدون `# noqa: F401` رها نکن.** یک بار ruff --fix اون import رو به‌عنوان «unused» حذف کرد، `Base.metadata` خالی موند، و autogenerate می‌خواست جدول‌های users/otp_challenge/refresh_tokens رو **drop** کنه. قبل از هر `alembic revision --autogenerate`، حتماً output رو بخون و مطمئن شو فقط «Detected added» می‌بینی، نه «Detected removed» روی جدول‌های موجود.
2. `alembic.ini` از قبل `prepend_sys_path = .` داره؛ نیازی به دستکاری دستی `sys.path` در `env.py` نیست.
3. نصب پکیج از PyPI گاهی timeout می‌ده (شبکه‌ی این محیط ناپایدار است) — با `--default-timeout=60 --retries 5-10` و اجرای پس‌زمینه (`run_in_background`) دوباره امتحان کن؛ عموماً دفعه‌ی دوم/سوم جواب می‌ده.
4. نصب Playwright/Chromium با خطای ۴۰۳ جغرافیایی مسدود می‌شه (`cdn.playwright.dev`) — کاربر گفته قبلاً در پروژه‌ی دیگه‌ای (moviesite) موفق نصب شده، پس شاید موقتیه؛ برای تست بصری فعلاً از `curl`/بررسی HTML خام استفاده کن.
5. فونت Kalameh **تجاری/مالکیتی** است (fontiran.com) و کد لایسنس ۶رقمی‌اش پر نشده. کاربر صریحاً گفته با همین حال فایل‌ها رو نگه دار و ریپو رو public کن — تصمیم آگاهانه‌ی کاربره، دوباره ازش سؤال نکن. پوشه‌ی خام `/font/` (سورس اصلی وندور) در `.gitignore` هست و کامیت نمی‌شه؛ فقط `frontend/src/fonts/kalameh/*.woff2` (فایل‌های واقعاً استفاده‌شده) کامیت شدن.
6. یک `package.json`/`node_modules/` ناخواسته (پکیج `agentation`) در ریشه‌ی ریپو (نه داخل frontend/) توسط ابزار محیط ساخته شده، ربطی به پروژه نداره — در `.gitignore` مستثنا شده (`/node_modules/`, `/package.json`, `/package-lock.json` با `/` پیشرو یعنی فقط ریشه، نه `frontend/`).
7. endpoint دقیق IPPanel (`app/providers/sms/ippanel.py`) از مستندات رسمی تأیید **نشده** (سایتشون JS-render هست، WebFetch نتونست بخونه) — بر اساس الگوی متداول نوشته شده؛ قبل از استفاده‌ی واقعی با API key واقعی تست/تطبیق بده. Kavenegar و Brevo مستقیماً از داک رسمی تأیید شدن.
8. تست‌ها به Redis/DB واقعی نیاز ندارن — `tests/conftest.py` از `fakeredis` و یک SQLite موقت (`tmp_path`) استفاده می‌کنه؛ CI بدون Docker هم پاس می‌شه.
9. برای دیدن OTP واقعی در تست، از لاگ متن استفاده نکن — `ConsoleSmsProvider`/`ConsoleEmailProvider` یک لیست `sent_messages` در حافظه دارن (`provider.sent_messages[-1]["message"]`)، پایدارتر از parse کردن caplog.
10. **موقع نصب pip در پس‌زمینه، خروجی رو مستقیم به `tail` پایپ نکن.** یک بار `pip install ... | tail -20` گزارش "exit code 0" داد چون `tail` موفق بود، نه `pip` (که واقعاً به‌خاطر timeout شبکه شکست خورده بود و پکیج اصلاً نصب نشده بود) — بعداً `from app.main import app` fail کرد چون `python-multipart` غایب بود. همیشه بعد از نصب پس‌زمینه‌ای، با `pip show <package>` مستقل تأیید کن، نه فقط به کد خروجی task notification اعتماد کن.
11. **Limiter عمومی slowapi حافظه‌ی in-process داره** (نه Redis-backed) — در تست‌ها اگه بین تست‌ها ریست نشه، یک endpoint با سقف پایین (مثلاً ۱۰-۲۰/دقیقه) بعد از چند تست پشت‌سرهم واقعاً ۴۲۹ برمی‌گردونه و تست‌های بعدی رو به‌طور نامرتبط fail می‌کنه. فیکسچر `autouse` در `conftest.py` (`_reset_rate_limiter`) این رو حل می‌کنه — اگه فیکسچر رو حذف/تغییر دادی حواست باشه.
12. **همیشه بعد از نوشتن endpointهای عمومی/بدون احراز هویت، از خودت بپرس «آیا وضعیت DRAFT/CANCELLED هم از این مسیر قابل دیدنه؟»** — این دقیقاً همون باگی بود که در فاز ۲ حین نوشتن تست integration کشف و رفع شد (نگاه کن به بخش «وضعیت فعلی» بالا).

## تصمیمات کلیدی کاربر (خلاصه‌ی فشرده — کامل در architecture.md)

- تقویم: نمایش شمسی در UI، ذخیره‌ی UTC/میلادی در DB (هنوز پیاده نشده در فرانت، فاز بعدی)
- Vector search: ChromaDB (نه Qdrant)
- فرانت: Next.js با SSR برای صفحات عمومی رویداد (نه SPA خالص) — به‌خاطر SEO
- سفارش تک‌نفره (بدون خرید گروهی)
- ایجاد رویداد بدون تأیید ادمین، فقط rate-limit
- کد تخفیف: هم سطح رویداد هم سطح سایت (ادمین)
- دسته‌بندی: دوسطحی (نه تخت) — رویداد فقط زیردسته انتخاب می‌کنه
- آپلود بنر: حتماً re-encode امن (بخش ۱۶) — نگرانی صریح کاربر از ویروس/steganography
- سایت باید کاملاً ریسپانسیو باشه

## مرجع‌های بیرونی مهم

- `docs/event_otp_email_sms_plan_fa.md` — سند اصلی مکانیزم OTP (کاربر نوشته، منبع حقیقت برای پارامترهای OTP)
- `data/eseminar.tv/analysis.md`, `data/evand.com/analysis.md` — تحلیل رقبا، پایه‌ی بسیاری از تصمیمات UX
