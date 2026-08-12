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
| رنگ برند | سبز `#2E9E4F` (primary)، قرمز `#DA1A32` (destructive)، navy تیره `#161826` (پس‌زمینه‌ی dark mode) — دقیقاً از `logo/royaevent-logo.svg`، تبدیل‌شده به oklch در `globals.css` (`--brand-green/red/dark`) |

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
  backend/tests/unit|integration/   # pytest، fakeredis، بدون نیاز به Redis واقعی — فاز ۳ هنوز تست نداره
  frontend/src/
    app/
      (auth)/login/page.tsx        # ورود OTP (client)
      (organizer)/events/create/   # فرم ایجاد رویداد (client)
      (organizer)/events/mine/     # لیست رویدادهای من (client)
      events/page.tsx              # لیستینگ عمومی (SSR/dynamic)
      events/[slug]/page.tsx       # جزئیات رویداد عمومی (SSR/dynamic + JSON-LD)
      page.tsx                     # خانه
    components/EventCard.tsx       # کارت رویداد (Server Component)
    components/RoyaEventLogo.tsx   # لوگوی متنی برند (سبز/سفید/قرمز)
    components/RoyaEventLoader.tsx # اسپلش‌اسکرین، وصل به app/loading.tsx (Suspense خودکار نکست‌جس)
    components/SiteHeader.tsx      # هدر مشترک (لوگو+ناوبری)، در layout ریشه
    components/ui/                 # shadcn primitives (+ textarea, select)
    lib/
      api-client.ts    # fetch wrapper سمت کلاینت، credentials:include، پشتیبانی FormData
      events-api.ts     # انواع TS + توابع کلاینت events/categories (نیاز به accessToken)
      events-server.ts  # فراخوانی سمت سرور برای RSC (cache:"no-store"، بدون کوکی)
      date.ts            # formatJalali* — Intl بومی fa-IR-u-ca-persian، بدون کتابخانه‌ی جانبی
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
- **فاز ۲ (Event CRUD + دسته‌بندی/تگ/جلسه + آپلود بنر امن)** ✅ **کامل (بک‌اند + فرانت‌اند)، تست‌شده، لینت تمیز، تأیید بصری end-to-end. همه commit/push شده (بک‌اند، فرانت، لوگو/اسپلش‌اسکرین، تم رنگی برند).**
- **فاز ۳ (بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن)** 🚧 **بک‌اند: مدل‌ها + migration + schemas + services + همه‌ی routerها نوشته و در main.py wire شدن (۳۶ route کل، verify شده با openapi schema). هنوز uncommitted، هنوز تست نداره، فرانت شروع نشده.** جزئیات کامل زیر. **این‌جا متوقف شد — ادامه از این نقطه.**
- فازهای ۴ تا ۱۱: هنوز شروع نشده (جستجو، ادمین، اعلان‌ها، امتیازدهی، آنالیتیکس، مانیتورینگ، تست/RTL نهایی، دیپلوی).

**بک‌اند در مجموع الان ۱۰۱ تست دارد (unit + integration، فاز ۳ صفر تست اضافه کرده هنوز)، همه پاس، `ruff check .` تمیز، migration تا آخر (`956ea659d2be`) verify شده.** فرانت `npm run build` و `npm run lint` هر دو تمیز.

**تأیید بصری واقعی فاز ۲ (نه فقط build/test):** بک‌اند و فرانت هر دو به‌صورت real dev server بالا آورده شدن، دسته‌بندی‌ها seed شدن، از طریق OTP واقعی لاگین شد، یک رویداد واقعی از طریق API ساخته و publish شد، و HTML خروجی SSR صفحات `/events` و `/events/[slug]` با `curl` بررسی شد — عنوان فارسی، تاریخ شمسی، دسته‌بندی، JSON-LD همه درست رندر شدن. (Playwright برای اسکرین‌شات واقعی مرورگر هنوز در دسترس نیست — نگاه کن به دام #۴.) **فاز ۳ هنوز این‌جور تأیید نشده — اول باید فاز ۳ تست/build بشه.**

### فاز ۳ — بک‌اند wired اما تست‌نشده (نقطه‌ی ادامه‌ی کار)

**نوشته‌شده (uncommitted):**
- مدل‌ها: `TicketType` (با `is_early_bird`)، `DiscountCode` (سطح رویداد)، `PlatformDiscountCode` (سطح سایت/ادمین)، `Order`/`OrderItem`/`Payment`/`Registration`، `Favorite`، `OrganizerFollow`/`InstructorFollow` — `app/models/ticket.py`, `order.py`, `favorite.py`
- Migration `956ea659d2be` روی پایه‌ی `567deeea1757` — اجرا و verify شد (فقط create، بدون drop)
- `app/services/ticket_service.py` — `is_early_bird_active(event)`: طبق نیازمندی ۳۴ («اگر کمتر از یک‌سوم بازه‌ی شروع فروش تا اولین جلسه گذشته باشد»)؛ مرجع «شروع رویداد» = زودترین جلسه (ساده‌سازی برای رویداد چندجلسه‌ای)
- `app/services/discount_service.py` — `find_valid_discount()` اول سطح رویداد بعد سطح سایت رو چک می‌کنه؛ `compute_discount_amount()` percent/fixed
- `app/services/order_service.py` — `create_order()` (اعتبارسنجی ticket/session/ظرفیت/early-bird/تخفیف، PENDING می‌سازه)، `complete_order()` (finalize، Registration با ticket_code یکتا می‌سازه، quantity_sold رو +۱ می‌کنه، uses_count تخفیف رو +۱)، `cancel_registration()` (ظرفیت رو برمی‌گردونه)
- `app/services/social_service.py` — toggle ساده برای favorite/organizer-follow/instructor-follow
- `app/core/calendar.py` — `google_calendar_link()`: تابع محض تولید URL، بدون OAuth (طبق تصمیم کاربر)
- `app/core/permissions.py` — `require_event_owner()` منتقل شد این‌جا (قبلاً تکراری در events.py بود)؛ `app/services/event_service.py` هم `event_query()`/`to_list_item_out()` عمومی شدن (قبلاً private در events.py) تا `social.py` هم بتونه ازشون استفاده کنه برای `/me/favorites`
- Routerها: `tickets.py` (ticket-types CRUD + discount-codes رویداد/ادمین + validate)، `orders.py` (create/complete/get/me-tickets/cancel/calendar-link)، `social.py` (favorites + follows)، `organizer.py` (attendees list/remove/export CSV)
- همه در `main.py` wire شدن؛ مجموعاً ۳۶ route (بررسی‌شده با `app.openapi()['paths']`)

**هنوز نیاز به تکمیل (فردا از این‌جا ادامه بده):**
1. **هیچ تستی برای فاز ۳ نوشته نشده** — نه unit (ticket_service/discount_service/order_service/social_service) نه integration (tickets/orders/social/organizer API). این اولین کاریه که باید فردا انجام بشه، قبل از commit.
2. بعد از نوشتن تست‌ها: `pytest` کامل + `ruff check .` (احتمالاً نیاز به فیکسچرهای جدید در conftest.py مثل `ticket_type`/`published_event` مشابه الگوی `leaf_category`).
3. فرانت فاز ۳ اصلاً شروع نشده: صفحه‌ی چک‌اوت/انتخاب بلیط، دکمه‌ی علاقه‌مندی/دنبال‌کردن روی کارت/صفحه‌ی رویداد، فوتر چسبان «انتخاب بلیط» (نیازمندی ۳۷)، داشبورد شرکت‌کنندگان برگزارکننده، صفحه‌ی «بلیط‌های من».
4. بعد از تکمیل، تأیید بصری end-to-end واقعی مثل فاز ۲ (seed + OTP + ساخت ticket_type + خرید واقعی + بررسی HTML) قبل از commit نهایی.
5. `docs/architecture.md` بخش ۱۴ باید بعد از تکمیل فاز ۳ به‌روزرسانی بشه.
6. **این commit فعلی (اگه همین الان زده بشه) یک checkpoint نیمه‌کاره‌ست، نه «فاز ۳ کامل»** — پیام commit باید صادقانه این رو نشون بده (مثل فاز ۱/۲ که فقط بعد از تست‌شدن کامل commit شدن).

### فاز ۲ — کامل (بک‌اند + فرانت‌اند)

**بک‌اند:**
- مدل‌ها: `Category` (دوسطحی، self-FK)، `Tag`، `Instructor`، `Event`، `EventSession`، جدول‌های M:N `event_tags`/`event_instructors`
- Alembic migration `567deeea1757` روی پایه‌ی `07c06a1dc198` — `alembic upgrade head` تست شده، جدول‌ها verify شدند (`categories, tags, events, instructors, event_instructors, event_sessions, event_tags` + جدول‌های فاز ۱)
- `app/db/seed_categories.py` — ۱۰ دسته‌ی والد × ۳-۵ زیردسته (اجرا: `python -m app.db.seed_categories`) — **در محیط dev واقعی اجرا و ۴۶ ردیف verify شد.** یک باگ Windows-only پیدا و رفع شد: کنسول ویندوز پیش‌فرض `cp1252` است و `print()` متن فارسی رو با `UnicodeEncodeError` crash می‌کرد (بعد از این‌که commit شده بود روی DB — یعنی داده درست ذخیره می‌شد، فقط پیام پایانی fail می‌کرد)؛ فیکس با `sys.stdout.reconfigure(encoding="utf-8")` قبل از `print`.
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

**فرانت‌اند (کامل، build+lint تمیز، uncommitted):**
- `lib/date.ts` — تاریخ شمسی با `Intl.DateTimeFormat("fa-IR-u-ca-persian", ...)` بومی (بدون dayjs/jalaliday؛ Node این محیط ICU کامل داره، تست شد). این جایگزین چیزیه که در `docs/architecture.md` («dayjs + پلاگین جلالی») نوشته شده بود — سبک‌تره و کار می‌کنه، ولی سند رسماً به‌روز نشده (اگه لازم شد یادت باشه).
- `lib/events-api.ts` (کلاینت) و `lib/events-server.ts` (Server Components، `cache:"no-store"`) — جدا نگه داشته شدن چون سرور نیازی به کوکی/accessToken نداره.
- `components/EventCard.tsx` — کارت رویداد با blur/badge «این وبینار برگزار شده است» برای جلسه‌ی گذشته، badge «ویژه»، رتبه.
- `app/events/page.tsx` و `app/events/[slug]/page.tsx` — **حتماً dynamic (SSR per-request)، نه ISR/SSG.** اول با `next:{revalidate:60}` نوشته شده بود که باعث می‌شد `npm run build` سعی کنه در build-time به بک‌اند وصل بشه و چون بک‌اند بالا نبود، build کامل fail می‌کرد. با `cache:"no-store"` در `events-server.ts` حل شد (Next خودکار این route ها رو به `ƒ Dynamic` تشخیص می‌ده). **اگه یه فایل fetch جدید سمت سرور نوشتی، همین الگو رو رعایت کن، وگرنه build دوباره می‌شکنه.**
- `app/(organizer)/events/create/page.tsx` — فرم ایجاد رویداد (client، چندبخشی: اطلاعات پایه، دسته‌بندی با گروه‌بندی والد/زیردسته، جلسه‌های دینامیک، بعد از ایجاد → آپلود بنر اختیاری → انتشار).
- `app/(organizer)/events/mine/page.tsx` — لیست رویدادهای من با دکمه‌ی انتشار سریع برای پیش‌نویس‌ها.
- shadcn `Select` (بر پایه‌ی Base UI) امضای متفاوتی از Radix داره: `onValueChange: (value: string | null, details) => void` — همیشه `v && setState(v)` یا `v ?? fallback` بنویس، نه مستقیم `setState` (وگرنه TypeScript error می‌ده).

**نکات جزئی/اختیاری باقی‌مانده (بدون فوریت):**
- حداکثر حجم بنر (۵ مگابایت) در دو جا جدا hardcode شده — `MAX_BANNER_UPLOAD_BYTES` در `events.py` و `MAX_UPLOAD_BYTES` در `image_service.py`. یکسان‌اند، ولی بهتره یه‌جا (مثلاً `core/config.py`) متمرکز بشه.
- سند `docs/architecture.md` بخش ۱۲ هنوز «dayjs + پلاگین جلالی» رو به‌عنوان تصمیم ذکر می‌کنه؛ پیاده‌سازی واقعی از `Intl` بومی استفاده کرد (بالاتر توضیح داده شد) — عملکرد یکسانه، فقط مستندسازی sync نیست.
- کامیت فرانت فاز ۲ هنوز زده نشده (بک‌اند و CLAUDE.md قبلاً commit/push شدن).

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
13. **بدون `logging.basicConfig(...)`، لاگرهای خودمون (`ConsoleSmsProvider` و بقیه) در اجرای واقعی سرور اصلاً چاپ نمی‌شن** — چون root logger پیش‌فرض Python سطح `WARNING` داره و `.info(...)` صدا زده نمی‌شه، برخلاف تست‌ها که pytest caplog جدا رفتار می‌کنه. این باعث شد اولین تلاش برای گرفتن OTP از لاگ سرور واقعی (برای تست دستی) هیچی نشون نده. فیکس: `logging.basicConfig(level=logging.INFO, ...)` در بالای `app/main.py`. اگه لاگ چیزی رو نمی‌بینی، این رو اول چک کن.
14. **در Git Bash روی ویندوز، پاس‌دادن متن فارسی مستقیم داخل آرگومان `curl -d '...'` یا حتی داخل یک دستور `grep` می‌تونه بایت‌های چندبایتی UTF-8 رو به `?` خراب کنه** (مشاهده شد: یک رویداد تستی با `title` واقعاً به‌صورت `??????...` در دیتابیس ذخیره شد — این یک باگ اپلیکیشن نبود، چون همون لحظه ۱۰۱ تست pytest که رشته‌های فارسی رو in-process از فایل‌های `.py` می‌خونن بدون مشکل پاس می‌شدن). **راه‌حل امن برای تست دستی API با داده‌ی فارسی:** payload رو با ابزار Write در یک فایل UTF-8 بنویس، بعد `curl --data-binary @file.json` بزن — هرگز متن فارسی رو مستقیم در آرگومان shell تایپ نکن. برای grep/جست‌وجوی متن فارسی در خروجی هم به همین دلیل نتیجه‌ی نگرفتن لزوماً یعنی «پیدا نشد» نیست؛ با فایل/ابزار Read مطمئن‌تر چک کن.

## تصمیمات کلیدی کاربر (خلاصه‌ی فشرده — کامل در architecture.md)

- تقویم: نمایش شمسی در UI، ذخیره‌ی UTC/میلادی در DB — **پیاده شد** (`lib/date.ts`, فاز ۲) با `Intl` بومی، نه dayjs
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
