# CLAUDE.md — RoyaEvent

راهنمای جهت‌یابی سریع برای Claude Code در این ریپو. این فایل عمداً سبک نگه داشته می‌شه: فقط ساختار پروژه، استک فنی، قراردادها، و تصمیمات کلیدیِ پایدار. برای معماری کامل به [`docs/architecture.md`](docs/architecture.md) مراجعه کن. **برای وضعیت اجرایی هر فاز (چی ساخته شد، چه تستی نوشته شد، چه باگی پیدا و رفع شد) به [`specs/`](specs/README.md) مراجعه کن — هر فاز یک فایل `specN.md` جدا داره، آخرین فایل = آخرین وضعیت پروژه.**

## پروژه چیست

**RoyaEvent** — پلتفرم فارسی/RTL مدیریت رویداد و وبینار (شبیه eseminar.tv و evand.com، تحلیل رقبا در `data/`). صاحب پروژه: کاربر فارسی‌زبان، ارتباط همیشه به فارسی. کد/کامنت/پیام‌های کاربر همه فارسی‌اند مگر اسم فنی (متغیر، تابع) که انگلیسی می‌مونه.

مالک مخزن گیت‌هاب: `royajafari` (public) — https://github.com/royajafari/RoyaEvent

## وضعیت فعلی (خلاصه — جزئیات کامل در specs/)

| فاز | موضوع | وضعیت |
|---|---|---|
| ۰ | Scaffolding + مستندات | ✅ [`specs/spec0.md`](specs/spec0.md) |
| ۱ | Auth/OTP + JWT چرخشی | ✅ [`specs/spec1.md`](specs/spec1.md) |
| ۲ | CRUD رویداد + دسته‌بندی/تگ/جلسه + آپلود بنر امن | ✅ [`specs/spec2.md`](specs/spec2.md) |
| ۳ | بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن | ✅ [`specs/spec3.md`](specs/spec3.md) |
| ۴ | جستجو (ChromaDB) + صفحه‌ی اصلی | ⏳ شروع نشده |
| ۵ | پنل ادمین | ⏳ شروع نشده |
| ۶ | اعلان‌ها + زمان‌بند + لینک تقویم | ⏳ شروع نشده |
| ۷ | امتیاز/نظر ۴محوره + علاقه‌مندی تکمیلی | ⏳ شروع نشده |
| ۸ | آنالیتیکس/KPI | ⏳ شروع نشده |
| ۹ | استک مانیتورینگ | ⏳ شروع نشده |
| ۱۰ | تقویت تست + مقاومت آفلاین/RTL | ⏳ شروع نشده |
| ۱۱ | آماده‌سازی دیپلوی VPS (TLS/HTTPS اجباری — نگاه کن به بخش تصمیمات) | ⏳ شروع نشده |

بک‌اند در مجموع الان **۱۷۳ تست** دارد (unit+integration)، همه پاس، `ruff check .` تمیز. فرانت `npm run build`، `npx eslint src --max-warnings=0` و `npx tsc --noEmit` هر سه تمیز.

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
| فونت | Kalameh (محلی، `frontend/src/fonts/kalameh/*.woff2`، فایل تجاری — نکته‌ی لایسنس در `specs/spec0.md`) |
| رنگ برند | سبز `#2E9E4F` (primary)، قرمز `#DA1A32` (destructive)، navy تیره `#161826` — دقیقاً از `logo/royaevent-logo.svg`، تبدیل‌شده به oklch در `globals.css` (`--brand-green/red/dark`). **کل سایت به‌صورت دائمی تم تیره (navy) داره** (کلاس `dark` روی `<html>` در `layout.tsx`) تا با پس‌زمینه‌ی لوگو یکی باشه — به درخواست کاربر، نه یک toggle قابل‌تغییر. |

## ساختار پوشه‌ها

```
RoyaEvent/
  backend/app/
    api/v1/routers/   # auth.py, events.py, tickets.py, orders.py, social.py, organizer.py
    api/deps.py        # get_db, get_current_user, get_current_admin_user, get_redis, get_sms/email_provider, get_client_ip
    core/               # config, security (JWT+OTP hash), rate_limit (OTP), rate_limit_middleware (عمومی/slowapi)
                        # redis_client, storage (MinIO), slug, validators, calendar (لینک گوگل‌کلندر)، permissions (require_event_owner)
    db/                 # session.py (engine/Base/get_db)، migrations/ (Alembic)، seed_categories.py
    models/             # User, OTPChallenge, RefreshToken, Category, Tag, Instructor, Event, EventSession,
                        # TicketType, DiscountCode, PlatformDiscountCode, Order, OrderItem, Payment, Registration,
                        # Favorite, OrganizerFollow, InstructorFollow
    providers/sms|email/ # base + console(dev) + ippanel/kavenegar/brevo/resend
    schemas/            # auth.py, event.py, ticket.py, order.py, social.py, organizer.py (Pydantic)
    services/           # otp_service, auth_service, event_service (+event_query/to_list_item_out عمومی),
                        # image_service, ticket_service, discount_service, order_service, social_service
  backend/tests/unit|integration/   # pytest، fakeredis، بدون نیاز به Redis واقعی
  frontend/src/
    app/
      (auth)/login/page.tsx        # ورود OTP (client)
      (organizer)/events/create/   # فرم ایجاد رویداد (client)
      (organizer)/events/mine/     # لیست رویدادهای من (client)
      (organizer)/organizer/events/[id]/attendees/  # داشبورد شرکت‌کنندگان + export CSV (client)
      events/page.tsx              # لیستینگ عمومی (SSR/dynamic)
      events/[slug]/page.tsx       # جزئیات رویداد عمومی (SSR/dynamic + JSON-LD + چک‌اوت/فوتر چسبان/favorite/follow)
      tickets/page.tsx             # «بلیط‌های من» (client)
      page.tsx                     # خانه
    components/EventCard.tsx       # کارت رویداد (Server Component)
    components/TicketCheckout.tsx, StickyTicketFooter.tsx, FavoriteButton.tsx, FollowOrganizerButton.tsx  # فاز ۳ (client)
    components/RoyaEventLogo.tsx   # لوگوی متنی برند (سبز/سفید/قرمز)
    components/RoyaEventLoader.tsx # اسپلش‌اسکرین، وصل به app/loading.tsx (Suspense خودکار نکست‌جس)
    components/SiteHeader.tsx      # هدر مشترک (لوگو+ناوبری)، در layout ریشه
    components/ui/                 # shadcn primitives (+ textarea, select)
    lib/
      api-client.ts    # fetch wrapper سمت کلاینت، credentials:include، پشتیبانی FormData
      events-api.ts     # انواع TS + توابع کلاینت events/categories (نیاز به accessToken)
      events-server.ts  # فراخوانی سمت سرور برای RSC (cache:"no-store"، بدون کوکی)
      tickets-api.ts, orders-api.ts, social-api.ts, organizer-api.ts  # فاز ۳
      date.ts            # formatJalali* — Intl بومی fa-IR-u-ca-persian، بدون کتابخانه‌ی جانبی
    store/auth-store.ts  # Zustand، access token فقط در حافظه
    fonts/kalameh.ts
  infra/docker-compose.yml   # redis, mongo, minio, loki, prometheus, grafana
  data/eseminar.tv/, data/evand.com/   # تحلیل رقبا
  docs/architecture.md        # پلن کامل معماری (مرجع اصلی طراحی)
  docs/event_otp_email_sms_plan_fa.md  # سند اولیه‌ی OTP (کاربر داده، مرجع دقیق مکانیزم OTP)
  specs/                       # تاریخچه‌ی اجرای فازها — یک specN.md به‌ازای هر فاز (نگاه کن به specs/README.md)
```

## کارهای درخواستی در صف (خارج از نقشه‌ی راه اصلی، هنوز شروع نشده)

کاربر این‌ها رو مستقیم درخواست داده؛ باید قبل از فاز ۴ یا در کنارش انجام بشن:

1. **آپلود کلیپ کوتاه تبلیغاتی رویداد** (کنار بنر، نه جایگزین) — فیلد جدید `promo_video_url` روی `events` (migration ساده، افزایشی)؛ محدودیت حجم سخت‌گیرانه (پیشنهاد: ۲۰-۳۰ مگابایت)، فرمت محدود به MP4/WebM بر اساس **magic bytes** (نه پسوند/Content-Type کلاینت — طبق همون منطق امنیتی بنر در بخش ۱۶ پلن)، بدون transcode واقعی در MVP (ffmpeg سنگینه، فعلاً فقط اعتبارسنجی+ذخیره در MinIO با نام تصادفی)، نمایش با `<video controls preload="metadata">` در صفحه‌ی رویداد. برگزارکننده می‌تونه بنر، کلیپ، یا هر دو رو بذاره.
2. **تور آموزشی سایت (onboarding tour)** برای بازدیدکننده‌ی اولین‌بار — معرفی امکانات کلیدی سایت با یک کتابخونه‌ی سبک (مثلاً driver.js/react-joyride)، نمایش یک‌بار (چک با `localStorage`)، قابل رد‌کردن/تکرار دستی.
3. **TLS/HTTPS اجباری در production** — از قبل بخشی از فاز ۱۱ (Nginx reverse proxy + Let's Encrypt، ریدایرکت خودکار HTTP→HTTPS) بود؛ کاربر صراحتاً تأکید کرد. در `docker-compose.prod.yml` و راهنمای دیپلوی فاز ۱۱ باید کامل مستند/پیاده بشه، نه فقط اشاره.

## قراردادهای API

- Base path: `/api/v1` (از `settings.api_v1_prefix`)
- Auth: `Authorization: Bearer <access_token>` برای access token (در حافظه‌ی فرانت، نه localStorage)؛ refresh token در کوکی httpOnly به اسم `refresh_token` (مسیر `/`)
- خطاها: `HTTPException` با پیام فارسی؛ برای OTP/Auth عمداً پیام‌های عمومی (بدون افشای این‌که کاربر/OTP وجود داره یا نه)
- همه‌ی مدل‌های زمانی در DB **naive UTC** هستن (نه timezone-aware) — SQLite مقایسه‌ی aware/naive رو با TypeError رد می‌کنه؛ همیشه از `app.models.base.utcnow()` استفاده کن، نه `datetime.now(timezone.utc)` مستقیم
- Provider abstraction: کد سرویس هرگز مستقیم IPPanel/Kavenegar/Brevo/Resend صدا نمی‌زنه؛ از `get_sms_provider()`/`get_email_provider()` (factory، بر اساس `.env`) رد می‌شه. بدون API key، خودکار می‌ره روی `ConsoleProvider` (فقط لاگ، برای dev/test)
- **قاعده‌ی دائمی (از باگ امنیتی فاز ۲):** بعد از نوشتن هر endpoint عمومی/بدون احراز هویت که رویداد یا هر رکورد دارای وضعیت (status) برمی‌گردونه، از خودت بپرس «آیا وضعیت DRAFT/CANCELLED هم از این مسیر قابل دیدنه؟» — جزئیات حادثه در `specs/spec2.md`.

## قراردادهای UI

- همه‌چیز RTL: `dir="rtl" lang="fa"` روی `<html>` (در `app/layout.tsx`)
- فونت: فقط Kalameh (`next/font/local`)، نه فونت دیگه
- کامپوننت‌های پایه از shadcn/ui؛ توجه: این نسخه‌ی shadcn روی **Base UI** ساخته شده نه Radix، پس `Button` پراپ `asChild` نداره — برای رندر به‌عنوان لینک از `buttonVariants({...})` روی `<Link>` مستقیم استفاده کن (نمونه در `frontend/src/app/page.tsx`)؛ `Select` هم امضای متفاوتی از Radix داره: `onValueChange: (value: string | null, details) => void` — همیشه `v && setState(v)` یا `v ?? fallback` بنویس.
- **ریسپانسیو الزامیه** (درخواست صریح کاربر) — mobile-first، از breakpointهای Tailwind استفاده کن، هر صفحه‌ی جدید رو حداقل در دو اندازه چک کن
- State سرور: TanStack Query (هنوز نصب/استفاده نشده، طرح فقط در پلنه) + Zustand برای state خالص کلاینت (فقط `auth-store.ts` فعلاً)
- صفحات عمومی رویداد/دسته‌بندی باید dynamic SSR باشن (`cache:"no-store"` در fetch سمت سرور)، نه ISR/SSG — وگرنه `npm run build` سعی می‌کنه در build-time به بک‌اند وصل بشه و بدون بک‌اند بالا fail می‌کنه.

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

پورت‌ها: API=8000، Next=3000، Redis=6379، Mongo=27017، MinIO=9000/9001(console)، **Loki=3100** (نه فرانت!)، Prometheus=9090، Grafana=3300 (نه 3000، تصادم با Next dev).

## نکات عملیاتی همیشگی (در هر فاز ممکنه دوباره پیش بیان)

این‌ها محدود به یک فاز خاص نیستن؛ دام‌های مخصوص یک فاز در همون `specs/specN.md` ثبت شدن.

1. **متن فارسی رو هرگز مستقیم داخل آرگومان shell (مثل `curl -d '...'`) روی Git Bash ویندوز تایپ نکن** — بایت‌های چندبایتی UTF-8 به `?` خراب می‌شن (یه رویداد تستی این‌جوری با عنوان `??????` در DB ذخیره شد؛ باگ اپلیکیشن نبود، چون تست‌های pytest که رشته‌های فارسی رو in-process از `.py` می‌خونن مشکلی نداشتن). **راه‌حل امن:** payload رو با Write در یک فایل UTF-8 بنویس، بعد `curl --data-binary @file.json` بزن. برای grep متن فارسی در خروجی هم همین قانون صادقه — نتیجه‌ی نگرفتن لزوماً یعنی «پیدا نشد» نیست.
2. **سرور uvicorn بدون `--reload` بعد از هر تغییر کد بک‌اند دستی باید restart بشه**، وگرنه نتیجه‌ی قدیمی برمی‌گردونه. برای نشست‌های تأیید بصری طولانی، `--reload` بزن یا حتماً بعد از ادیت بک‌اند سرور رو manual restart کن.
3. **پورت ۳۱۰۰ متعلق به Loki است، نه فرانت.** اگه با `curl localhost:3100` روی «404 page not found» ساده (نه HTML نکست‌جس) خوردی، یعنی داری Loki رو صدا می‌زنی. پورت واقعی Next dev همیشه در خروجی ترمینال `next dev` چاپ می‌شه، به همون اعتماد کن.
4. **بدون `logging.basicConfig(...)` در `app/main.py`، لاگرهای خودمون در اجرای واقعی سرور چاپ نمی‌شن** (root logger پیش‌فرض Python سطح `WARNING` داره) — این فیکس از فاز ۱ در `main.py` هست؛ اگه لاگ چیزی نشون نمی‌ده، این رو چک کن.
5. **Next.js App Router الزام می‌کنه همه‌ی route های هم‌سطح روی یک segment، اسم پارامتر dynamic یکسانی داشته باشن** (route groups مثل `(organizer)` در URL نامرئی‌ان). قبل از افزودن هر route جدید با پارامتر dynamic، چک کن آیا segment هم‌نامش جای دیگه با اسم پارامتر متفاوت قبلاً تعریف شده — جزئیات حادثه در `specs/spec3.md`.
6. **دانلود فایلی که نیاز به `Authorization: Bearer` داره رو نمی‌شه با `<a href>` مستقیم زد** — با `fetch`+`blob()`+`URL.createObjectURL` انجامش بده (نمونه: `organizer-api.ts: downloadAttendeesCsv`).
7. نصب پکیج از PyPI گاهی timeout می‌ده (شبکه‌ی این محیط ناپایدار است) — با `--default-timeout=60 --retries 5-10` و اجرای پس‌زمینه دوباره امتحان کن. **موقع نصب پس‌زمینه‌ای، خروجی رو مستقیم به `tail` پایپ نکن** (کد خروجی `tail` می‌تونه موفق باشه حتی اگه `pip` واقعاً fail شده باشه) — بعد از هر نصب پس‌زمینه‌ای با `pip show <package>` مستقل تأیید کن.
8. نصب Playwright/Chromium با خطای ۴۰۳ جغرافیایی مسدود می‌شه (`cdn.playwright.dev`) — برای تست بصری فعلاً از `curl`/بررسی HTML خام استفاده کن، نه اسکرین‌شات مرورگر واقعی.
9. `alembic.ini` از قبل `prepend_sys_path = .` داره؛ نیازی به دستکاری دستی `sys.path` در `env.py` نیست. **همیشه `import app.models` رو در `alembic/env.py` با `# noqa: F401` نگه دار** — حذف خودکارش توسط ruff باعث می‌شه `Base.metadata` خالی بمونه و autogenerate جدول‌های موجود رو drop کنه. قبل از هر `alembic revision --autogenerate`، output رو بخون و مطمئن شو فقط «Detected added» می‌بینی.
10. یک `package.json`/`node_modules/` ناخواسته (پکیج `agentation`) ممکنه در ریشه‌ی ریپو (نه داخل `frontend/`) توسط ابزار محیط ساخته بشه — در `.gitignore` مستثناست، نادیده بگیرش.

## تصمیمات کلیدی کاربر (خلاصه‌ی فشرده — کامل در architecture.md)

- تقویم: نمایش شمسی در UI، ذخیره‌ی UTC/میلادی در DB — پیاده شد (`lib/date.ts`) با `Intl` بومی، نه dayjs
- Vector search: ChromaDB (نه Qdrant)
- فرانت: Next.js با SSR برای صفحات عمومی رویداد (نه SPA خالص) — به‌خاطر SEO
- سفارش تک‌نفره (بدون خرید گروهی)
- ایجاد رویداد بدون تأیید ادمین، فقط rate-limit
- کد تخفیف: هم سطح رویداد هم سطح سایت (ادمین)
- دسته‌بندی: دوسطحی (نه تخت) — رویداد فقط زیردسته انتخاب می‌کنه
- آپلود بنر: حتماً re-encode امن (بخش ۱۶ پلن) — نگرانی صریح کاربر از ویروس/steganography
- کد رویداد: فرمت `RE-XXXXXX` (پیشوند برند RoyaEvent + ۶ رقم تصادفی)
- سایت باید کاملاً ریسپانسیو باشه
- تم سایت همیشه تیره (navy برند)، نه توگل روشن/تیره
- TLS/HTTPS اجباری در production (فاز ۱۱)

## مرجع‌های بیرونی مهم

- `docs/event_otp_email_sms_plan_fa.md` — سند اصلی مکانیزم OTP (کاربر نوشته، منبع حقیقت برای پارامترهای OTP)
- `data/eseminar.tv/analysis.md`, `data/evand.com/analysis.md` — تحلیل رقبا، پایه‌ی بسیاری از تصمیمات UX
- `specs/README.md` — قرارداد نگهداری فایل‌های spec، بخون قبل از نوشتن spec فاز جدید
