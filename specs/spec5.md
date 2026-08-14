# فاز ۵ — پنل ادمین

وضعیت: ✅ کامل (بک‌اند + فرانت‌اند)، تست‌شده، لینت/build تمیز، تأیید بصری end-to-end واقعی انجام‌شده.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی (refresh token بعداً از ۳۰ روز به ۱ روز کم شد). فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن + سیستم مدرس/آواتار/تکمیل پروفایل اجباری. فاز ۴: جستجوی معنایی (ChromaDB) + صفحه‌ی اصلی Redis-cached + ثبت‌نام فوری + پروفایل عمومی برگزارکننده. جمعاً ۲۲۰ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec4.md`](spec4.md).

## هدف

ادمین بتونه رویدادها رو مدیریت کنه (شامل حذف کامل هر رویدادی، نه فقط رویدادهای خودش)، کاربرها رو تعلیق/رفع‌تعلیق کنه، دسته‌بندی‌ها رو CRUD کنه، و هر اقدامش لاگ بشه.

## چیزی که ساخته شد

### بک‌اند

- **`admin_audit_log`** (مدل جدید + migration `9a216cb37dcf`): `admin_user_id, action, target_type, target_id, reason`. هر endpoint نوشتنی زیر `/admin` بعد از موفقیت، `admin_service.log_action(...)` رو صدا می‌زنه.
- **`GET /admin/events`**: برخلاف لیستینگ عمومی (`event_service.event_query`) که فقط PUBLISHED+PUBLIC رو نشون می‌ده، اینجا همه‌ی رویدادها (شامل DRAFT/CANCELLED/PRIVATE) قابل دیدنن.
- **`DELETE /admin/events/{id}`**: حذف **کامل و برگشت‌ناپذیر** — نه لغو نرم مثل چیزی که خود organizer با `cancel_event` می‌تونه. چون `orders/order_items/payments/registrations/ticket_types/discount_codes/favorites` بدون `ON DELETE CASCADE` سطح DB به `events.id` وصل‌ان، `admin_service.delete_event_completely` قبل از حذف خود رویداد، این جدول‌ها رو به ترتیب صریح (registrations → payments/order_items/orders → favorites/ticket_types/discount_codes) پاک می‌کنه، بعد `remove_event()` (حذف از ایندکس جستجو) و `db.delete(event)`.
- **`PATCH /admin/events/{id}/feature`**: تغییر `is_featured` — همون فیلدی که فاز ۴ برای بخش «ویژه»‌ی صفحه‌ی اصلی استفاده می‌کرد (قبلاً fallback موقتی بر اساس محبوبیت برگزارکننده داشت؛ الان با این endpoint می‌شه واقعی‌ش کرد).
- **`GET /admin/users` + `PATCH /admin/users/{id}/suspend`**: `UserStatus.SUSPENDED` از فاز ۱ تو مدل تعریف شده بود ولی **هیچ‌جا enforce نمی‌شد** — این باگ کشف و رفع شد (نه بخشی از این فاز، یه side-effect لازم برای این‌که تعلیق واقعاً کار کنه):
  - `verify_otp` (`routers/auth.py`): اگه کاربر تعلیق‌شده باشه، لاگین جدید با پیام روشن رد می‌شه (نه فقط توکن نده، صریح بگه چرا).
  - `AuthService.get_user_from_access_token`: access tokenهای از قبل صادرشده (تا ۱۵ دقیقه معتبرن) هم بلافاصله باطل می‌شن.
  - `AuthService.refresh`: جلوگیری از گرفتن access token تازه با یه refresh token چرخشی که هنوز منقضی نشده (تا ۱ روز معتبره).
  - ادمین نمی‌تونه خودش رو تعلیق کنه (۴۰۰).
- **CRUD `/admin/categories`**: `create/update` با `slugify_ascii` (همون الگوی get-or-create تگ/مدرس)، `delete` دو گارد داره: نه زیردسته داشته باشه، نه رویدادی بهش وصل باشه (۴۲۲ با پیام روشن، نه خطای FK خام).
- **`GET /admin/audit-log`**: آخرین ۱۰۰ اقدام، با اسم ادمین (`relationship` جدید `AdminAuditLog.admin_user`).
- Rate limit: `300/دقیقه` روی همه‌ی endpointهای `/admin` طبق بخش ۶ architecture.md (سقف بالا، فقط برای جلوگیری از اسکریپت رهاشده).
- **۱۱ تست جدید (۲۳۱ در مجموع)**: رد غیرادمین (۴۰۳) و ناشناس (۴۰۱)، لیست شامل DRAFT، حذف کامل (با و بدون سفارش واقعی مرتبط — تست جدا برای مسیر cascade)، toggle ویژه، جلوگیری از خودتعلیقی، تعلیق کاربر و قطع فوری هم لاگین جدید هم توکن قبلی، CRUD دسته‌بندی (شامل رد حذف دسته‌ی دارای رویداد).

### فرانت‌اند

- `lib/admin-api.ts` — کلاینت تمام endpointهای بالا.
- `app/admin/page.tsx` — یک داشبورد تب‌دار (`Tabs` موجود، Base UI) با ۴ تب: رویدادها (حذف با `window.confirm` چون برگشت‌ناپذیره + toggle ویژه)، کاربران (تعلیق/رفع‌تعلیق، دکمه برای نقش ادمین غیرفعال)، دسته‌بندی‌ها (فرم افزودن با انتخاب والد + لیست با حذف)، لاگ اقدامات (فقط نمایشی).
- لینک «پنل ادمین» در `SiteHeader` فقط وقتی `user?.role === "admin"` نشون داده می‌شه؛ خود صفحه هم دوباره چک می‌کنه (`user.role !== "admin"` → پیام «فقط برای ادمین») تا مستقیم‌رفتن به `/admin` بدون لینک هم محافظت‌شده باشه.

## نکات/دام‌های این فاز

- **مدل جدید (`AdminAuditLog`) به `app/models/__init__.py` اضافه نشده بود** — اولین `alembic revision --autogenerate` یه migration کاملاً خالی (`pass`/`pass`) تولید کرد، بدون هیچ خطایی. تشخیص داده شد چون خروجی autogenerate پیام «Detected added table» نداشت؛ migration خالی پاک شد، مدل به `__init__.py` اضافه شد، autogenerate دوباره اجرا شد و این‌بار درست کار کرد. جزئیات کامل در نکته‌ی #۲۰ CLAUDE.md.
- **همون دام #۱۹ (react-hooks/set-state-in-effect) دوباره پیش اومد** تو `app/admin/page.tsx: loadAll()` — این‌بار فیکس ساده‌تر بود: چون `loading` از قبل با `useState(true)` مقداردهی اولیه شده بود، صرفاً حذف فراخوانی زائد `setLoading(true)` از ابتدای `loadAll()` کافی بود (نیازی به بازطراحی effect نبود).
- **حذف کامل رویداد با سفارش واقعی مرتبط** یه ریسک FK/یتیم‌ماندن داشت که فقط با نوشتن یه تست اختصاصی (`test_admin_delete_event_with_orders_cascades`، که واقعاً یه سفارش کامل می‌سازه قبل از حذف) کشف/تأیید می‌شد — تست ساده‌ای که فقط رویداد بدون سفارش حذف می‌کرد این باگ رو نشون نمی‌داد.

## راستی‌آزمایی

بک‌اند و فرانت هر دو real dev server، `231 passed` (`pytest`)، `ruff check .` و `npx eslint src --max-warnings=0` تمیز، `npm run build` موفق (dev server بعدش با `.next` تازه ری‌استارت شد). یه کاربر ادمین تستی مستقیم تو DB ساخته شد (`09300000001`) و با `curl` روی سرور واقعی: `GET /admin/events` (۶ رویداد واقعی، شامل draft)، `GET /admin/users` (۶ کاربر)، `GET /admin/categories` (۴۶ دسته)، `PATCH .../feature` (تغییر واقعی + ثبت درست تو audit-log با اسم فارسی ادمین)، `GET /admin/audit-log` — همه تأیید شدن. صفحه‌ی `/admin` هم مستقیم با `curl` روی frontend dev server تأیید شد (رندر می‌شه، متن «پنل ادمین» تو HTML هست).

## Commitهای مرتبط

`7ecbd47` (بک‌اند: پنل ادمین)، `6b44fa4` (فرانت: پنل ادمین)

### بعد از فاز — صفحه‌ی ویرایش محتوای رویداد + کشف و رفع باگ جدی «هنگ کردن PATCH»

کاربر خودش رو با حساب واقعی (`09127993369`) ادمین کرد (مستقیم در DB، بدون endpoint خودسرویس — تصمیم امنیتی عمدی) و پرسید آیا می‌تونه محتوای یک رویداد (عنوان/توضیحات/دسته/جلسه‌ها) رو ویرایش کنه. بررسی نشون داد بک‌اند از قبل (`PATCH /events/{id}` + `PUT /events/{id}/sessions`) این کارو با `require_event_owner` پشتیبانی می‌کرد (که صراحتاً ادمین رو هم مجاز می‌دونه: `user.role.value != "admin"` در گارد رد دسترسی)، ولی **هیچ فرم فرانتی براش نبود** — فقط بنر/کلیپ (`/media`) و بلیط (`/tickets`) صفحه‌ی ویرایش داشتن. کاربر با «آره، الان تکمیل ش کن» تأیید کرد.

- **`app/(organizer)/organizer/events/[id]/edit/page.tsx`** (جدید): فرم کامل ویرایش — عنوان، توضیحات، دسته‌بندی (Combobox)، نوع برگزاری، آدرس/پلتفرم آنلاین، سیاست بازگشت وجه، تگ‌ها، مدرس‌ها، ثبت‌نام فوری، و آرایه‌ی جلسه‌ها (افزودن/حذف/ویرایش، همون الگوی `create/page.tsx`). چون سشن‌ها بخشی از `EventUpdateIn` نیستن، ثبت فرم دو فراخوانی جدا و متوالی می‌زنه: `eventsApi.update(...)` (PATCH، بدون سشن) بعد `eventsApi.replaceSessions(...)` (PUT، جایگزینی کامل آرایه‌ی سشن). قابل‌دسترس هم برای مالک رویداد (از `events/mine`) هم برای ادمین (از `/admin`، تب رویدادها) — بدون نیاز به endpoint یا صفحه‌ی جدای ادمین.
- `lib/events-api.ts`: تابع `replaceSessions` اضافه شد (PUT به `/events/{id}/sessions`).
- لینک «ویرایش» به `events/mine/page.tsx` و `admin/page.tsx` (تب رویدادها) اضافه شد.

**باگ جدی کشف‌شده حین تست زنده (نه بخشی از درخواست اولیه، اما مستقیماً مانع کارکرد درست فیچر بود):** تست زنده‌ی `PATCH /events/6` (رویداد منتشرشده) با `curl` چند دقیقه هنگ کرد و اصلاً پاسخ نداد. علتش: `update_event`/`publish_event`/`cancel_event` (`event_service.py`) به‌صورت sync `sync_event_index()` رو صدا می‌زدن که مدل embedding (فاز ۴، `sentence-transformers`) رو لود می‌کنه؛ روی شبکه‌ی ناپایدار این محیط، دانلود اولیه‌ی مدل (~۴۷۰ مگابایت) نه واقعاً قطع می‌شد نه کامل می‌شد — فقط بی‌نهایت کند trickle می‌کرد. سه تلاش برای فیکس:

1. **try/except دور `sync_event_index`** (نسخه‌ی از قبل موجود) — شکست خورد: `timeout 20 curl ...` کد خروجی ۱۲۴ (timeout) داد، چون trickle کند هیچ‌وقت واقعاً exception نمی‌ده که try/except بگیرتش.
2. **`HF_HUB_DOWNLOAD_TIMEOUT=5`** (env var، در `app/search/embeddings.py`) — شکست خورد: بازم `timeout 25 curl` کد ۱۲۴ داد؛ چک لاگ بک‌اند (`tail -30`) تأیید کرد دانلود هنوز فعالانه در حال خوندن chunk بود، پس semantics تایم‌اوت خوندن روی یه اتصال کند-ولی-زنده اصلاً تریگر نمی‌شه.
3. **`ThreadPoolExecutor` + `future.result(timeout=3)`** (فیکس نهایی، `event_service.py`) — موفق: `_safe_sync_event_index` حالا خود `sync_event_index` رو تو یه executor جدا (`_INDEX_EXECUTOR`, `max_workers=2`) submit می‌کنه و حداکثر ۳ ثانیه (`_INDEX_TIMEOUT_SECONDS`) صبر می‌کنه؛ اگه تموم نشد فقط warning لاگ می‌کنه و ادامه می‌ده (thread پس‌زمینه بی‌ضرر رها می‌شه چون فقط property اسکالر از قبل لود‌شده‌ی event رو می‌خونه، نه رابطه‌ای که به session زنده نیاز داشته باشه). تأیید زنده: `time curl -X PATCH .../events/6` → `HTTP:200 TIME:3.326054s`، دقیقاً منطبق با تایم‌اوت تنظیم‌شده.

این کشف باعث شد یه اصل کلی‌تر مستند بشه (نکته‌ی #۲۱ CLAUDE.md): **«try/except دور یه فراخوانی» فقط زمانی کمک می‌کنه که اون فراخوانی واقعاً exception بده — اگه فقط بی‌نهایت کند باشه (نه fail نه موفق)، تنها راه واقعی محدودسازی با timeout رو یه thread/process جدا بستنه.** یه تست واحد جدید هم اضافه شد (`test_publish_does_not_block_on_slow_search_indexing` در `tests/unit/test_event_service.py`) که `sync_event_index` رو با یه `time.sleep(_INDEX_TIMEOUT_SECONDS + 5)` مصنوعی جایگزین می‌کنه و تأیید می‌کنه `publish_event` هنوز ظرف چند ثانیه برمی‌گرده — این تست به‌طور دترمینیستیک (بدون وابستگی به شبکه‌ی واقعی) دقیقاً همون سناریوی هنگ رو شبیه‌سازی و از رگرسیون آینده محافظت می‌کنه.

داده‌ی تستی خراب‌شده حین این verification (یه `refund_policy` فارسی که با curl مستقیم در Git Bash تایپ شد و به `???` خراب شد — همون باگ شناخته‌شده‌ی encoding، نه باگ اپ) مستقیم با اسکریپت پایتون در DB پاک شد.

راستی‌آزمایی نهایی: `ruff check .` تمیز، `pytest -q` → **۲۳۲ تست پاس** (۲۳۱ قبلی + ۱ تست جدید resilience).

### Commitهای این بخش

`9cfaec1` (فیکس: جلوگیری از هنگ کردن PATCH/publish/cancel رویداد با ایندکس جستجوی async با timeout)، `f638a28` (فرانت: صفحه‌ی ویرایش محتوای رویداد برای مالک/ادمین)
