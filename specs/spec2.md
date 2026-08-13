# فاز ۲ — CRUD رویداد + دسته‌بندی/تگ/جلسه + آپلود بنر امن

وضعیت: ✅ کامل (بک‌اند + فرانت‌اند)، تست‌شده، لینت تمیز، تأیید بصری end-to-end.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه + docker-compose + مستندات. فاز ۱: احراز هویت OTP-only کامل، JWT چرخشی، ۵۵ تست پاس. جزئیات: [`spec0.md`](spec0.md)، [`spec1.md`](spec1.md).

## هدف

برگزارکننده بتونه رویداد (تک/چندجلسه‌ای) با دسته‌بندی/تگ/بنر بسازه و منتشر کنه؛ صفحه‌ی عمومی رویداد با SEO (SSR + JSON-LD).

## چیزی که ساخته شد

**بک‌اند:**
- مدل‌ها: `Category` (دوسطحی، self-FK — رویداد فقط زیردسته/برگ انتخاب می‌کنه)، `Tag`، `Instructor`، `Event`، `EventSession`، جدول‌های M:N `event_tags`/`event_instructors`.
- Alembic migration `567deeea1757` روی پایه‌ی `07c06a1dc198`.
- `app/db/seed_categories.py` — ۱۰ دسته‌ی والد × ۳-۵ زیردسته (اجرا: `python -m app.db.seed_categories`)، در dev واقعی اجرا و ۴۶ ردیف verify شد.
- `app/services/image_service.py` — `validate_and_reencode_image()`: magic-byte check با Pillow، رد SVG، محدودیت ۵MB/۴۰۰۰px، همیشه خروجی JPEG تازه (حتی ورودی PNG/WebP) با flatten روی پس‌زمینه‌ی سفید، حذف کامل EXIF/متادیتا — طبق نگرانی صریح کاربر از ویروس/steganography در فایل آپلودی (بخش ۱۶ پلن). ۹ تست، شامل تست این‌که payload الحاقی به انتهای فایل در خروجی نیست.
- `app/core/storage.py` — کلاینت MinIO + `ensure_bucket_ready()` (public-read) + `upload_banner_image()` — در تست mock می‌شه، نیازی به MinIO واقعی برای تست نیست.
- `app/core/slug.py` — `slugify_ascii()` + کد رویداد ۶رقمی تصادفی (**این فرمت بعداً در فاز ۳ به `RE-XXXXXX` تغییر کرد — نگاه کن به [`spec3.md`](spec3.md)**).
- `app/services/event_service.py` — create/update/publish/cancel event، replace_sessions، تولید slug/event_code یکتا، اعتبارسنجی این‌که category باید برگ باشه، get-or-create برای تگ‌ها.
- `app/api/v1/routers/events.py` — `GET/POST /events`, `GET /events/mine`, `GET /events/id/{id}` (فقط مالک، DRAFT رو هم می‌ده)، `GET /events/code/{code}`, `GET /events/private/{token}`, `GET /events/{slug}` (فقط PUBLISHED)، `GET /events/{id}/related`, `PATCH/DELETE /events/{id}`, `PUT /events/{id}/sessions`, `POST /events/{id}/publish`, `POST /events/{id}/banner`, `GET /events/categories`.
- `app/core/rate_limit_middleware.py` — Limiter عمومی slowapi (کلید = user_id اگه لاگین باشه وگرنه IP، سقف پیش‌فرض ۱۲۰/دقیقه)؛ روی `create_event`/`update_event`/`replace_event_sessions` سقف ۲۰/دقیقه، `upload_event_banner` سقف ۱۰/دقیقه. سه endpoint اختصاصی OTP (`otp/request`, `otp/resend`, `otp/verify`) همگی `@limiter.exempt` دارن (محدودیت خودشون رو از فاز ۱ دارن).

**رفع یک باگ امنیتی واقعی حین نوشتن تست integration:** اولین نسخه‌ی `get_event_by_slug`/`get_event_by_code`/`get_private_event` فقط `visibility` رو چک می‌کردن، نه `status` — یعنی رویداد **DRAFT منتشرنشده از طریق slug عمومی قابل مشاهده بود** (نشتی اطلاعات قبل از انتشار). اصلاح شد: هر سه endpoint حالا `status == PUBLISHED` رو هم الزامی می‌کنن. برای این‌که مالک هنوز بتونه پیش‌نویسش رو ببینه/ویرایش کنه، endpoint جدید `GET /events/id/{event_id}` (فقط مالک/ادمین، بدون محدودیت status) اضافه شد. **قاعده‌ی کلی که از این تجربه استخراج شد و در CLAUDE.md به‌عنوان قرارداد دائمی API ثبت شده:** بعد از نوشتن هر endpoint عمومی/بدون احراز هویت، از خودت بپرس «آیا وضعیت DRAFT/CANCELLED هم از این مسیر قابل دیدنه؟»

**تست‌ها:** `tests/unit/test_slug.py`, `test_image_service.py`, `test_event_service.py` + `tests/integration/test_events_api.py` (پوشش: auth، مالکیت/۴۰۳، DRAFT leak، publish idempotency، لیست عمومی در برابر `/mine`، رویداد خصوصی + توکن، آپلود بنر معتبر/نامعتبر/غیرمجاز، related events، دسته‌بندی‌ها). فیکسچرهای جدید در `conftest.py`: `organizer`, `auth_headers`, `leaf_category`، و یک `autouse` فیکسچر `_reset_rate_limiter` که `limiter.reset()` رو قبل/بعد هر تست صدا می‌زنه. مجموع تست تا این فاز: **۱۰۱**.

**فرانت‌اند:**
- `lib/date.ts` — تاریخ شمسی با `Intl.DateTimeFormat("fa-IR-u-ca-persian", ...)` بومی (بدون dayjs/jalaliday؛ سبک‌تره و کار می‌کنه — این جایگزین چیزیه که در `docs/architecture.md` («dayjs + پلاگین جلالی») نوشته شده بود، سند رسماً sync نشده ولی عملکرد یکسانه).
- `lib/events-api.ts` (کلاینت) و `lib/events-server.ts` (Server Components، `cache:"no-store"`) — جدا نگه داشته شدن چون سرور نیازی به کوکی/accessToken نداره.
- `components/EventCard.tsx` — کارت رویداد با blur/badge «این وبینار برگزار شده است» برای جلسه‌ی گذشته، badge «ویژه»، رتبه.
- `app/events/page.tsx` و `app/events/[slug]/page.tsx` — SSR per-request با JSON-LD schema.org/Event.
- `app/(organizer)/events/create/page.tsx` — فرم ایجاد رویداد (client، چندبخشی).
- `app/(organizer)/events/mine/page.tsx` — لیست رویدادهای من با دکمه‌ی انتشار سریع.
- لوگو/اسپلش‌اسکرین رسمی سایت (`RoyaEventLogo`, `RoyaEventLoader`) + تم رنگی برند در `globals.css` (سبز `#2E9E4F`، قرمز `#DA1A32`، navy `#161826`).

## نکات/دام‌های این فاز

- **هرگز `import app.models` رو در `alembic/env.py` بدون `# noqa: F401` رها نکن.** یک بار ruff --fix اون import رو به‌عنوان «unused» حذف کرد، `Base.metadata` خالی موند، و autogenerate برای migration این فاز می‌خواست جدول‌های `users`/`otp_challenge`/`refresh_tokens` (از فاز ۱) رو **drop** کنه. قبل از هر `alembic revision --autogenerate`، حتماً output رو بخون و مطمئن شو فقط «Detected added» می‌بینی، نه «Detected removed» روی جدول‌های موجود — این یک قاعده‌ی دائمیه، برای هر migration بعدی هم صادقه.
- کنسول ویندوز پیش‌فرض `cp1252` است و `print()` متن فارسی در `seed_categories.py` رو با `UnicodeEncodeError` crash می‌کرد (بعد از این‌که commit شده بود روی DB — یعنی داده درست ذخیره می‌شد، فقط پیام پایانی fail می‌کرد)؛ فیکس با `sys.stdout.reconfigure(encoding="utf-8")` قبل از `print`.
- **Limiter عمومی slowapi حافظه‌ی in-process داره** (نه Redis-backed) — در تست‌ها اگه بین تست‌ها ریست نشه، یک endpoint با سقف پایین بعد از چند تست پشت‌سرهم واقعاً ۴۲۹ برمی‌گردونه و تست‌های بعدی رو نامرتبط fail می‌کنه. فیکسچر `autouse` (`_reset_rate_limiter`) این رو حل کرد.
- `app/events/page.tsx` و `[slug]/page.tsx` **حتماً باید dynamic (SSR per-request) باشن، نه ISR/SSG.** اول با `next:{revalidate:60}` نوشته شده بود که باعث می‌شد `npm run build` سعی کنه در build-time به بک‌اند وصل بشه و چون بک‌اند بالا نبود، build کامل fail می‌کرد. با `cache:"no-store"` در `events-server.ts` حل شد. هر فایل fetch جدید سمت سرور باید همین الگو رو رعایت کنه.
- shadcn `Select` (بر پایه‌ی Base UI) امضای متفاوتی از Radix داره: `onValueChange: (value: string | null, details) => void` — همیشه `v && setState(v)` یا `v ?? fallback` بنویس، نه مستقیم `setState`.

## نکات جزئی باقی‌مانده (بدون فوریت)

- حداکثر حجم بنر (۵ مگابایت) در دو جا جدا hardcode شده — `MAX_BANNER_UPLOAD_BYTES` در `events.py` و `MAX_UPLOAD_BYTES` در `image_service.py`. یکسان‌اند، ولی بهتره یه‌جا (مثلاً `core/config.py`) متمرکز بشه.
- `docs/architecture.md` بخش ۱۲ هنوز «dayjs + پلاگین جلالی» رو ذکر می‌کنه؛ پیاده‌سازی واقعی از `Intl` بومی استفاده کرد.

## راستی‌آزمایی

بک‌اند و فرانت هر دو به‌صورت real dev server بالا اومدن، دسته‌بندی‌ها seed شدن، از طریق OTP واقعی لاگین شد، یک رویداد واقعی از طریق API ساخته و publish شد، و HTML خروجی SSR صفحات `/events` و `/events/[slug]` با `curl` بررسی شد — عنوان فارسی، تاریخ شمسی، دسته‌بندی، JSON-LD همه درست رندر شدن.

## Commitهای مرتبط

`a15ee36` (بک‌اند)، `d45de6b` (فیکس دو باگ dev)، `86ad5d0` (افزودن CLAUDE.md)، `a62b61d` (فرانت)، `687baad` (docs)، `ff7f340` (لوگو/اسپلش)، `f98e5df` (تم رنگی)
