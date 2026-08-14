# فاز ۶ — اعلان‌ها + زمان‌بند + لینک تقویم

وضعیت: ✅ کامل (بک‌اند)، تست‌شده، لینت تمیز، تأیید زنده روی DB واقعی dev انجام‌شده. فرانت این فاز UI مستقلی نداره (اعلان‌ها کاملاً پشت‌صحنه‌ان)، فقط یه تغییر رفتاری در پنل ادمین (حذف رویداد) هم‌زمان کنارش انجام شد.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن + سیستم مدرس/آواتار/تکمیل پروفایل اجباری. فاز ۴: جستجوی معنایی (ChromaDB) + صفحه‌ی اصلی Redis-cached + ثبت‌نام فوری. فاز ۵: پنل ادمین (رویدادها/کاربران/دسته‌بندی/لاگ اقدامات) + بعداً صفحه‌ی ویرایش محتوای رویداد + فیکس resilience ایندکس جستجو. جمعاً ۲۳۲ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec5.md`](spec5.md).

## هدف

بخش ۸ پلن معماری: وقتی کاربر ثبت‌نام/خرید بلیط تکمیل می‌کنه پیامک+ایمیل تأییدیه بگیره، و ۱ ساعت قبل از شروع هر جلسه یادآوری خودکار دریافت کنه — بدون این‌که این کار درخواست HTTP اصلی (تکمیل سفارش) رو کند یا مسدود کنه.

## چیزی که ساخته شد

### مدل/زیرساخت

- **`NotificationOutbox`** (مدل جدید، migration `f12505e8c94e`): `user_id, event_id(nullable), channel(sms/email), destination, template_key, payload_json, status(pending/sent/failed), attempts, next_attempt_at, provider, provider_message_id, last_error`. صف مشترک هر ۳ قالب — دقیقاً طبق بخش ۸ پلن.
- **`app/core/persian_date.py`**: `format_jalali_datetime(dt)` — تبدیل UTC ذخیره‌شده در DB به ساعت تهران (`zoneinfo`) و بعد به تقویم جلالی (`jdatetime`)، برای متن پیامک/ایمیل. این با `lib/date.ts` فرانت فرق داره: اونجا `Intl` مرورگر خودش timezone کاربر رو حدس می‌زنه، ولی سرور مرورگری نداره که این تبدیل رو خودکار انجام بده — باید صریح انجام بشه. وابستگی‌های جدید: `jdatetime==6.1.0`, `tzdata==2026.3` (تزدیتا لازمه چون نه ویندوز نه ایمیج‌های Docker slim دیتابیس IANA سیستمی دارن، `zoneinfo` بدونش fail می‌ده).
- **`app/services/notification_templates.py`**: قالب‌های Jinja2 برای هر ۳ `template_key` × ۲ کانال (SMS متن ساده و کوتاه چون فارسی UCS-2 هر پارت فقط ۷۰ کاراکتره؛ Email یک subject+body HTML ساده‌ی RTL).
- **`app/services/notification_service.py`**: `enqueue()` سطح پایه (یه ردیف به‌ازای هر مقصد در دسترس کاربر — اگه هم phone هم email داشته باشه، هر دو صف می‌شن)، و دو تابع سطح بالا: `notify_registration_complete()` (بسته به `pricing_model` بلیط، یا `REGISTRATION_COMPLETE` یا `TICKET_PURCHASE_COMPLETE` رو صف می‌کنه — چون این پروژه «ثبت‌نام» جدا از «خرید» نداره، هر دو همون لحظه‌ی `complete_order`ان) و `notify_event_reminder()`.
- **`app/workers/scheduler.py`**: پردازه‌ی جدا (`python -m app.workers.scheduler`)، `APScheduler.BlockingScheduler` با دو job:
  - `dispatch_outbox` (هر ۱۵ ثانیه، `notification_dispatch_interval_seconds`): صف `PENDING` با `next_attempt_at <= now` رو می‌خونه (batch ۵۰تایی)، از طریق `get_sms_provider()`/`get_email_provider()` واقعی ارسال می‌کنه، وضعیت رو آپدیت می‌کنه. شکست = backoff نمایی (`30 * 2^(attempts-1)`, سقف ۱ ساعت) تا `notification_max_attempts` (۵)، بعدش `FAILED`.
  - `scan_reminders` (هر ۶۰ ثانیه، `reminder_scan_interval_seconds`): `registrations` جوین `event_sessions`+`events` که `starts_at` بین ۵۹-۶۱ دقیقه‌ی آینده، `reminder_sent_at IS NULL`، `status=CONFIRMED`، و رویداد `PUBLISHED` باشه رو پیدا و صف می‌کنه، `reminder_sent_at` رو ست می‌کنه.
  - هر دو job با قفل Redis (`SET NX EX`, همون الگوی `enforce_cooldown` فاز ۱) محافظت می‌شن — برای وقتی این worker بعداً replica بشه.
  - هر دو تابع (`dispatch_outbox`, `scan_reminders`) پارامتر اختیاری `db: Session | None` دارن — در اجرای واقعی خالی صدا زده می‌شن (خودشون از `SessionLocal` واقعی می‌سازن)، در تست صریح session ایزوله‌ی تست تزریق می‌شه. این جداسازی لازم بود چون منطق داخلی این توابع session-agnostic نوشته شده، نه فقط برای APScheduler.
- **قلاب در `order_service.complete_order`**: بعد از commit سفارش، `notification_service.notify_registration_complete(...)` صدا زده می‌شه، تو `try/except` (نه thread/timeout مثل دام #۲۱ ایندکس جستجو — چون این فقط یه INSERT محلیه، نه I/O شبکه‌ای کند؛ اگه exception بده واقعاً سریع می‌ده، پس try/except اینجا کافی و درسته).
- تنظیمات جدید در `config.py`: `notification_dispatch_interval_seconds=15`, `reminder_scan_interval_seconds=60`, `notification_max_attempts=5`.
- لینک Google Calendar (بخش ۸ پلن) از فاز ۳ از قبل ساخته شده بود (`app/core/calendar.py`، بدون OAuth) — همین‌جا در payload ایمیل تأییدیه استفاده شد، کار اضافه‌ای لازم نبود.

### تغییر رفتاری هم‌زمان: حذف رویداد ادمین به soft-delete تبدیل شد

کاربر حین کار رو این فاز، مستقل از اعلان‌ها، خواست که دکمه‌ی «حذف کامل» پنل ادمین (فاز ۵) دیگه واقعاً ردیف رو از DB پاک نکنه — فقط منطقی (soft) حذف بشه و لاگش بمونه. این یه تغییر معماری عمدی روی تصمیم قبلی مستندشده در `spec5.md` بود (اونجا صریحاً «برگشت‌ناپذیر» طراحی شده بود). با migration `d27437f2f8af` ستون `events.deleted_at` اضافه شد:

- `admin_service.delete_event_completely` (که کلی cascade-delete دستی رو جدول‌های `registrations/payments/order_items/orders/favorites/ticket_types/discount_codes` داشت) با `soft_delete_event` جایگزین شد — فقط `event.deleted_at = utcnow()` + `remove_event()` (حذف از ایندکس جستجو) + commit. کل منطق cascade حذف شد (دیگه لازم نیست، چون رکورد اصلاً حذف نمی‌شه).
- `event_service.event_query()` (نقطه‌ی مشترک همه‌ی لیستینگ/جزئیات عمومی رویداد — events، search، home، related) یه `filter(Event.deleted_at.is_(None))` گرفت، پس رویداد soft-delete شده خودکار از همه‌جای عمومی ناپدید می‌شه.
- `admin_service.list_all_events` هم همین فیلتر رو گرفت، پس از لیست خود پنل ادمین هم می‌ره — دقیقاً همون تجربه‌ی «حذف شد» از دید کاربر، ولی داده واقعاً می‌مونه.
- `admin_audit_log` (که از قبل برای این اکشن نوشته می‌شد) الان واقعاً معنی داره چون `target_id` به یه رکورد واقعاً موجود اشاره می‌کنه، نه یه رکورد پاک‌شده.
- این تغییر باعث شد یه اثر جانبی مهم هم لازم بشه: چون این فاز `NotificationOutbox.event_id` رو به `events.id` FK کرد، تست قدیمی `test_admin_delete_event_with_orders_cascades` (که سناریوی hard-delete رو تست می‌کرد) دیگه با soft-delete معنی نداشت و به ۳ تست جدید بازنویسی شد (جزئیات پایین).

## نکات/دام‌های این فاز

- **`tzdata` روی ویندوز/Docker slim اجباریه، نه اختیاری**: `zoneinfo.ZoneInfo("UTC")` روی ویندوز بدون پکیج pip جدا `ZoneInfoNotFoundError` می‌ده (`No module named 'tzdata'`) چون ویندوز/بعضی ایمیج‌های Linux slim دیتابیس IANA سیستمی رو ندارن. این با لینوکس معمولی که معمولاً tzdata سیستمی داره فرق می‌کنه — روی هر محیطی که کد رو اجرا می‌کنی (dev محلی ویندوز، Docker prod)، اگه `zoneinfo` استفاده می‌کنی، `tzdata` pip package رو صریح وابستگی کن، به سیستم‌عامل اعتماد نکن.
- **تست‌هایی که `Registration` رو مستقیم با `order_item_id` جعلی می‌سازن (مثلاً `order_item_id=1` بدون این‌که واقعاً چنین `OrderItem`ای وجود داشته باشه) با `FOREIGN KEY constraint failed` fail می‌شن** — چون `db/session.py` صریحاً `PRAGMA foreign_keys=ON` داره (تصمیم قدیمی، نه چیز جدید این فاز)، ولی این فاز اولین بار بود که تست‌های جدید این الگوی جعلی رو امتحان کردن و باهاش برخوردن. فیکس درست: به‌جای ساختن `Registration` دستی، از `order_service.create_order`+`complete_order` واقعی استفاده کن تا کل زنجیره‌ی FK (`Order → OrderItem → Registration`) واقعی و معتبر باشه.
- **اضافه‌کردن FK جدید به یه جدول موجود (اینجا `NotificationOutbox.event_id → events.id`) می‌تونه کد cascade-delete جای دیگه‌ای رو که فکر می‌کردی کامل بود بشکنه** — `admin_service`ی قدیمی که قبل از این فاز کامل بود (همه‌ی جدول‌های وابسته رو صریح قبل از حذف event پاک می‌کرد) بعد از اضافه‌شدن این FK جدید دیگه ناقص بود و `test_admin_delete_event_with_orders_cascades` با `IntegrityError` fail کرد — تا وقتی که تصمیم گرفته شد اصلاً کل مسئله با soft-delete حل بشه (که این دسته کدها رو کاملاً حذف کرد، نه فقط پچ). این یه یادآوریه که هر FK جدید به `events`/`users`/هر جدول «مرکزی» دیگه، باید چک بشه آیا یه مسیر حذف hard-delete موجود جایی هست که باید ازش خبر داشته باشه.
- **الگوی session تزریقی برای worker functions**: چون `app/workers/scheduler.py` قراره به‌عنوان پردازه‌ی کاملاً جدا (نه از دل FastAPI) اجرا بشه، `dispatch_outbox`/`scan_reminders` نمی‌تونن از فیکسچر `db_session` تست‌ها استفاده کنن مگه این‌که صریح یه پارامتر `db: Session | None = None` بگیرن (پیش‌فرض خودشون `SessionLocal()` واقعی می‌سازن، تست صریح session تست رو پاس می‌ده). بدون این، تست باید یا مستقیم SQLite فایل واقعی رو دستکاری کنه (کثیف) یا اصلاً قابل تست نباشه.

## راستی‌آزمایی

- `ruff check .` تمیز، `pytest -q` → **۲۵۵ تست پاس** (۲۳۲ قبلی + ۲۳ تست جدید: enqueue/template rendering/notify_*/dispatch با provider fake/retry-backoff/scan_reminders با پنجره‌ی زمانی دستکاری‌شده + soft-delete).
- **تأیید زنده روی DB واقعی dev** (نه تست): یه ردیف واقعی `NotificationOutbox` (کانال SMS، قالب `EVENT_REMINDER_1H`) مستقیم در DB واقعی ساخته شد، `scheduler.dispatch_outbox()` یک‌بار مستقیم اجرا شد (بدون mock، با `get_redis()`/`get_sms_provider()` واقعی — که چون `.env` کلید IPPanel نداره خودکار رفت روی `ConsoleSmsProvider`)، خروجی لاگ نشون داد متن فارسی کامل (شامل تاریخ جلالی درست‌محاسبه‌شده‌ی «۲۲ مرداد ۱۴۰۵ ساعت ۱۴:۰۰») رندر و «ارسال» شد، و ردیف در DB به `status=SENT` با `provider=console` آپدیت شد. بعدش ردیف تست پاک شد (چون DB واقعی dev بود، نه یه‌بارمصرف).
- `scan_reminders` مستقیم روی DB واقعی تست نشد (فقط unit test، نه manual) — چون منطق‌ش (پنجره‌ی زمانی + join + `_send_one` مشترک با `dispatch_outbox` که بالا تأیید زنده شد) قبلاً با ۴ تست اختصاصی که مستقیم همون کد `scan_reminders(db=...)` رو صدا می‌زنن پوشش داده شده، و ساختن یه سناریوی زنده‌ی کامل (event+session+order+registration واقعی که دقیقاً ۱ ساعت دیگه شروع بشه) روی DB dev ریسک آلوده‌کردن داده‌ی واقعی رو داشت بدون فایده‌ی اضافه‌ی قابل‌توجه.

## Commitهای مرتبط

commitهای بک‌اند این فاز (مدل/migration/سرویس/worker/تست‌ها/soft-delete) به‌صورت یک‌جا در پایان این فاز commit و push شدن (نگاه کن به تاریخچه‌ی گیت اطراف تاریخ این فایل). commitهای فرانت هم‌زمان (استایل جدول رویدادهای پنل ادمین: layout/رنگ/pagination/جستجو) کاملاً مستقل و بی‌ربط به منطق اعلان‌هان، جدا commit شدن.
