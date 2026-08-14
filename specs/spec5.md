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
