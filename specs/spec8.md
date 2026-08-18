# فاز ۸ — آنالیتیکس/KPI

وضعیت: ✅ کامل (بک‌اند + فرانت + پنل ادمین)، تست‌شده، لینت/تایپ تمیز، زنده روی سرور dev تأیید شد.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن + سیستم مدرس/آواتار/تکمیل پروفایل اجباری. فاز ۴: جستجوی معنایی (ChromaDB) + صفحه‌ی اصلی Redis-cached + ثبت‌نام فوری. فاز ۵: پنل ادمین (رویدادها/کاربران/دسته‌بندی/لاگ اقدامات). فاز ۶: صف اعلان‌ها (SMS/Email) + worker زمان‌بند + یادآوری ۱ساعته + soft-delete رویداد. فاز ۷: امتیاز/نظر ۴محوره رویداد + امتیاز ساده مدرس/برگزارکننده/سایت. جمعاً ۲۸۷ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec7.md`](spec7.md).

## هدف

بخش ۳ و ۱۱ پلن معماری: یک بیکن سبک فرانت رفتار خام کاربر (بازدید صفحه، جستجو، قدم‌های قیف ثبت‌نام) رو در Mongo لاگ کنه، یک job شبانه این لاگ خام رو با کوئری‌های SQLite ترکیب و در یک جدول رول‌آپ (`kpi_daily_snapshot`) خلاصه کنه، و پنل ادمین یک گزارش قابل‌فهم از این خلاصه نشون بده — بدون این‌که هیچ‌کدوم از این‌ها مسیر اصلی درخواست کاربر رو کند یا fail کنه.

## چیزی که ساخته شد

### بک‌اند

- **`app/core/mongo_client.py`**: `get_mongo_db()` (`lru_cache`، `serverSelectionTimeoutMS=2000` — اگه Mongo پایین باشه، درخواست اصلی کاربر معطل نمی‌مونه) + وایرینگ در `app/api/deps.py`. تنظیمات `mongo_uri`/`mongo_db_name` و سرویس `mongo` در `infra/docker-compose.yml` از فازهای قبل آماده بودن، فقط کد مصرف‌کننده‌ش نبود.
- **`POST /api/v1/track`** (`app/api/v1/routers/track.py`، rate-limit `120/minute`): بدنه‌ی `{event_type, session_id, payload}` — `event_type` یکی از `page_view | search_query | funnel_step | click` است. `app/services/track_service.py: record_event` هر کدوم رو به کالکشن Mongo متناظر (`page_views` / `search_queries` / `funnel_events` / `click_events`، دقیقاً طبق بخش ۳ پلن) می‌نویسه؛ `user_id` اگه کاربر لاگین‌کرده باشه (`get_current_user_optional`) خودکار اضافه می‌شه. هر خطای نوشتن Mongo بی‌صدا catch می‌شه (`try/except` ساده، نه ThreadPoolExecutor مثل دام #۲۱ ایندکس جستجو — چون `insert_one` با timeout کوتاه خودش سریع fail می‌ده، نه بی‌نهایت آویزون بمونه).
- **`KpiDailySnapshot`** (مدل جدید، migration `ce839d60b434`): `snapshot_date, metric_name, dimensions_json, value` با `UniqueConstraint` روی هر سه تا (upsert-friendly، مثل الگوی `rating_service`).
- **`app/services/kpi_service.py`**:
  - `rollup_daily_kpis(db, mongo_db, target_date)`: قیف `VIEW_EVENT → CLICK_REGISTER → START_CHECKOUT → COMPLETE_ORDER` (شمارش هر قدم از `funnel_events`) + نرخ تبدیل بازدید-به-تکمیل، کل/شکست جستجو + ۵ کلیدواژه‌ی پرتکرار (از `search_queries`)، DAU (تعداد `session_id` یکتای `page_views`)، سلامت قیف OTP (`otp_requested`/`otp_verified`، مستقیم از `OTPChallenge` موجود در SQLite — نیازی به Mongo نداره).
  - `get_kpi_report(db, days)`: خوندن ساده از `kpi_daily_snapshot` برای گزارش ادمین — خود گزارش هیچ‌وقت مستقیم سراغ Mongo نمی‌ره، فقط به سلامت SQLite وابسته‌ست.
- **job شبانه در `app/workers/scheduler.py`**: `rollup_kpis()` با تریگر `cron` (پیش‌فرض `۰۰:۰۰ UTC` = `۰۳:۳۰` بامداد تهران، ترافیک کم)، قفل Redis مثل بقیه‌ی jobها، همیشه **دیروز** رو رول‌آپ می‌کنه (نه امروز، چون رفتار امروز هنوز کامل نشده).
- **`GET /admin/reports/kpis?days=`** (فقط‌خواندنی) + **`POST /admin/reports/kpis/rollup`** (بدنه‌ی اختیاری `{date}`، پیش‌فرض دیروز — برای بک‌فیل/تست دستی بدون صبر تا اجرای شبانه؛ چون اقدام صریح ادمینه، `admin_service.log_action("manual_kpi_rollup", ...)` صدا زده می‌شه).
- **`mongomock`** به `requirements.txt` اضافه شد (مثل `fakeredis` برای Redis) — تست‌ها به Mongo واقعی وابسته نیستن. فیکسچر `fake_mongo` در `tests/conftest.py`.
- **۱۵ تست جدید** (`tests/unit/test_kpi_service.py` + integration در `test_admin_api.py`): محاسبه‌ی قیف/نرخ تبدیل، صفر بودن نرخ تبدیل بدون بازدید، کلیدواژه‌های پرتکرار، DAU از session یکتا، سلامت OTP از SQLite، **upsert نه duplicate** (رول‌آپ دوباره‌ی همون روز مقدار قبلی رو overwrite می‌کنه نه insert جدید)، فیلتر بازه‌ی روزها، رد غیرادمین، و لیست شدن بعد از enqueue واقعی حین تکمیل سفارش. جمعاً **۳۰۸ تست پاس**.

### فرانت‌اند

- **`lib/track.ts`**: `track(eventType, payload)` — `navigator.sendBeacon` اول (fire-and-forget واقعی، حتی موقع ناوبری/بستن تب کار می‌کنه)، `fetch(..., {keepalive:true})` fallback. `session_id` تصادفی (`crypto.randomUUID()`) در `localStorage` (کلید `roya_session_id`) یک‌بار تولید و نگه‌داری می‌شه.
- **`PageViewTracker.tsx`** (در `layout.tsx` ریشه، بدون UI، مثل `SessionBootstrap`): هر تغییر `usePathname()` یک `page_view`.
- **`EventViewTracker.tsx`**: قدم `VIEW_EVENT` قیف، روی صفحه‌ی جزئیات رویداد.
- **`SearchQueryTracker.tsx`**: هر جستجوی واقعی + تعداد نتیجه (`result_count=0` = جستجوی بی‌نتیجه‌ی بخش ۱۱ پلن).
- **`TicketCheckout.tsx` و `InstantRegisterModal.tsx`** (هر دو مسیر ثبت‌نام سایت): `CLICK_REGISTER` (کلیک دکمه/باز شدن مودال)، `START_CHECKOUT` (قبل از `POST /orders`)، `COMPLETE_ORDER` (بعد از تکمیل موفق سفارش) — قیف کامل حالا از هر دو مسیر داده‌ی واقعی می‌گیره، نه فقط چک‌اوت معمولی.
- **تب «آمار و KPI» در پنل ادمین** (`app/admin/page.tsx`): همون جدول silver + جستجو + lazy loading بقیه‌ی تب‌ها؛ دکمه‌ی «محاسبه‌ی دوباره‌ی دیروز» (`POST .../rollup`) برای تست/بک‌فیل زنده؛ سوییچ **روزانه/ماهانه** — نمای ماهانه سمت کلاینت از همون داده‌ی روزانه‌ی fetch‌شده (بازه‌ی ۱۸۰ روز) محاسبه می‌شه، با گروه‌بندی بر اساس **ماه شمسی واقعی** (نه میلادی — هر روز جدا با `Intl` calendar=persian به ماه شمسی درستش نگاشت می‌شه، چون یک ماه میلادی معمولاً بین دو ماه شمسی تقسیم می‌شه)؛ نرخ تبدیل قیف در نمای ماهانه جمع/میانگین درصدهای روزانه نیست (ریاضی‌اش غلطه)، بلکه از مجموع بازدید/تکمیل سفارش همون ماه دوباره محاسبه می‌شه. تاریخ‌ها با `formatJalaliDate` نمایش داده می‌شن.

## نکات/دام‌های این فاز

- **`mongomock` جایگزین Mongo واقعی فقط در تست‌هاست، نه در dev/production** — سؤال مستقیم کاربر («چرا mongomock به‌جای خود Mongo؟») و پاسخ: دقیقاً همون دلیل `fakeredis` برای Redis — تست‌های این پروژه نباید به سرویس بیرونی واقعی وابسته باشن تا بدون نیاز به `docker compose up` هم پاس بشن. سرویس `mongo` واقعی در `infra/docker-compose.yml` دست‌نخورده موند.
- **نرخ تبدیل (یا هر معیار درصدی/نسبتی دیگه) هرگز نباید در بازه‌ی زمانی بزرگ‌تر (مثلاً روزانه→ماهانه) صرفاً جمع یا میانگین‌گیری بشه** — باید از صورت/مخرج اصلی (اینجا: مجموع `funnel_view_event`/`funne_complete_order` همون بازه) دوباره محاسبه بشه. این تنها معیاری بود که در `aggregateMonthlyKpis` فرانت به رفتار خاص نیاز داشت؛ بقیه‌ی معیارها (شمارش‌های ساده مثل DAU، تعداد جستجو) با جمع ساده درستن.
- **گروه‌بندی «ماهانه» بر اساس تقویم میلادی به‌جای شمسی، برای کاربر فارسی‌زبان گمراه‌کننده‌ست** — چون مرزهای ماه میلادی و شمسی یکی نیستن، باید هر روز جدا (نه کل بازه یک‌جا) با `Intl.DateTimeFormat(calendar: "persian")` به ماه شمسی خودش نگاشت بشه.
- **از یک ماژول دیگه import شده، `track()` هیچ‌وقت خودش setState صدا نمی‌زنه** — پس فراخوانی‌ش از دل `useEffect` (در `PageViewTracker`/`EventViewTracker`/`SearchQueryTracker`/`InstantRegisterModal`) دقیقاً همون الگوی امن `SessionBootstrap` رو دنبال می‌کنه و با قانون #۱۹ (`react-hooks/set-state-in-effect`) تداخل نداره.

## راستی‌آزمایی

- `ruff check .` تمیز، `pytest -q` → **۳۰۸ تست پاس**.
- فرانت: `npx eslint src --max-warnings=0` و `tsc --noEmit` تمیز.
- زنده روی سرور dev: بعد از restart دستی uvicorn، `/track` و `/admin/reports/kpis` در `openapi.json` تأیید شدن. دکمه‌ی «محاسبه‌ی دوباره‌ی دیروز» در پنل ادمین مستقیم تست شد و ردیف‌های واقعی (DAU، قیف، OTP) رو نشون داد — تأیید زنده‌ی کاربر با اسکرین‌شات.

## Commitهای مرتبط

- `ea334f8` — `feat(backend): فاز ۸ - آنالیتیکس/KPI (بیکن ردیابی + رول‌آپ شبانه + گزارش ادمین)`
- `544befe` — `feat(frontend): بیکن ردیابی فاز ۸ + قلاب قیف روی رویداد/چک‌اوت/جستجو`
- `6aef264` — `feat(frontend): تب «آمار و KPI» در پنل ادمین + روزانه/ماهانه + تاریخ شمسی`

(commitهای دیگه‌ی هم‌زمان این نشست — فیکس فیلتر دسته‌بندی والد، بخش «وبینارهای پیش‌رو» در صفحه‌ی اصلی، دکمه‌ی بررسی کد تخفیف، صفحه‌ی قوانین و مقررات، آیکون‌های تقویم/کپی‌لینک رویداد، نمایش اعداد فارسی — به فاز ۸ ربطی ندارن، جزئیاتشون در CLAUDE.md بخش «کارهای درخواستی در صف» ثبت شده.)
