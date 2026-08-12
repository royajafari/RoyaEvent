# RoyaEvent — معماری کامل پلتفرم مدیریت رویداد

> این سند، نسخه‌ی زنده‌ی پلن معماری تأییدشده در ابتدای پروژه است (فاز ۰). با پیشرفت فازها به‌روزرسانی می‌شه.

## Context (چرا این پروژه و چه چیزی قراره ساخته بشه)

کاربر می‌خواد یک پلتفرم مدیریت رویداد/وبینار فارسی‌زبان و کاملاً RTL به اسم **RoyaEvent** بسازه، مشابه دو رقیب ایرانی eseminar.tv و evand.com اما با قابلیت‌های اضافه (سیستم امتیازدهی ۴ محوره، پنل ادمین کامل، آنالیتیکس پشت‌صحنه، و غیره). قبل از شروع تولید کد، دو کار انجام شد:

1. **تحلیل رقبا** روی eseminar.tv و evand.com — نتایج در [`data/eseminar.tv/analysis.md`](../data/eseminar.tv/analysis.md) و [`data/evand.com/analysis.md`](../data/evand.com/analysis.md).
2. **مطالعه‌ی کامل** [`event_otp_email_sms_plan_fa.md`](event_otp_email_sms_plan_fa.md) که معماری OTP/Email/SMS رو از قبل به‌طور کامل مشخص کرده — این معماری عیناً و بدون تغییر در پلن زیر ادغام شده.

**تصمیمات کلیدی طول مکالمه:**
- تقویم: نمایش شمسی (جلالی) در UI، ذخیره‌سازی میلادی/UTC در دیتابیس.
- MongoDB: فقط برای رفتار کاربر + لاگ‌های تحلیلی (نه سیستم رکورد اصلی).
- Vector Search: **ChromaDB** (به‌جای Qdrant).
- مانیتورینگ: **Loki** + Prometheus + Grafana.
- Google Calendar: فقط لینک «افزودن به تقویم» (بدون OAuth).
- محیط توسعه: Docker Compose برای همه‌ی سرویس‌های جانبی.
- **فرانت‌اند: Next.js (SSR/Prerender)** به‌خاطر اهمیت SEO برای صفحات رویداد.
- فونت: **Kalameh** (فایل‌های محلی در `frontend/src/fonts/kalameh`).
- سفارش‌ها فعلاً تک‌نفره (بدون خرید گروهی چندبلیطی در یک سفارش).
- ایجاد رویداد بدون نیاز به تأیید ادمین؛ فقط Rate Limit به‌عنوان کنترل اسپم.
- کد تخفیف: هم سطح رویداد (توسط برگزارکننده) و هم سطح سایت (توسط ادمین، سراسری).

---

## 1. معماری کلی سیستم

```
                    ┌──────────────────────────┐
                    │  Next.js (App Router)     │
                    │  shadcn/ui, RTL, fa,       │
                    │  SSR/Prerender صفحات رویداد│
                    └────────────┬───────────────┘
                                 │ HTTPS (Nginx reverse proxy روی یک VPS)
                                 ▼
                    ┌──────────────────────────┐
                    │  FastAPI (Gunicorn+Uvicorn│  ← فقط پردازش request-time
                    │  workers, N>1)             │
                    └───┬──────┬──────┬──────────┘
                        │      │      │
          ┌─────────────┘      │      └───────────────┐
          ▼                    ▼                       ▼
  ┌───────────────┐   ┌───────────────┐        ┌───────────────┐
  │ SQLite (WAL)   │   │ Redis          │        │ MinIO (S3)     │
  │ منبع اصلی داده │   │ cache, rate-   │        │ بنر، آواتار،   │
  │ (کاربران،      │   │ limit، OTP     │        │ فایل‌های خروجی │
  │ رویدادها، ...) │   │ cooldown       │        └───────────────┘
  └───────────────┘   └───────────────┘
          │
          ▼ (write-through هنگام publish/update رویداد)
  ┌───────────────┐   ┌────────────────────────┐
  │ ChromaDB       │   │ MongoDB                 │
  │ (کتابخانه‌ی    │   │ آنالیتیکس رفتاری        │
  │ embedded،      │   │ (page_views, funnel,     │
  │ persisted vol) │   │ search_queries...)       │
  └───────────────┘   └────────────────────────┘

        ── پردازه‌ی جدا، خارج از worker‌های Gunicorn ──
  ┌───────────────────────────────────────────────────────────┐
  │  RoyaEvent Worker (یک پردازه/کانتینر اختصاصی)               │
  │  - APScheduler: اسکن یادآوری ۱ساعته (هر ۱ دقیقه)،             │
  │    دیسپچ صف اعلان (هر ۱۵ ثانیه)، رول‌آپ شبانه‌ی KPI            │
  │  - از SQLite + Redis می‌خونه/می‌نویسه (قفل توزیع‌شده SETNX)    │
  │  - Provider‌های SMS/Email رو برای ارسال واقعی صدا می‌زنه       │
  └───────────────────────────────────────────────────────────┘

  لایه‌ی مانیتورینگ (کانتینرهای سایدکار، همه در docker-compose):
  FastAPI → /metrics → Prometheus → Grafana
  FastAPI/Worker → لاگ ساختاریافته JSON → Loki (Promtail) → Grafana
```

**چرا APScheduler و نه Celery:** حجم job محدود و کاملاً دوره‌ای است (چند job، نه گراف پیچیده‌ی توزیع‌شده)؛ صحت job‌ها از طریق وضعیت دیتابیس تضمین می‌شه (مثلاً ستون `reminder_sent_at IS NULL`)، نه وضعیت اسکجولر — پس worker می‌تونه هر وقت crash/restart کنه بدون ریسک duplicate/missed. اگر بعداً بار افزایش پیدا کرد، الگوی `notification_outbox` سازگار با مهاجرت به Celery هست.

**نکته‌ی امنیتی مهم:** APScheduler باید فقط در یک پردازه اجرا بشه؛ اگر worker container بعداً replica شد، هر job با قفل Redis (`SET NX EX`) محافظت بشه.

---

## 2. Vector Search: ChromaDB

**تصمیم نهایی: ChromaDB embedded** (کتابخانه‌ی Python داخل پردازه‌ی FastAPI/Worker، ذخیره‌سازی روی یک Docker volume).

دلیل: بدون بار عملیاتی اضافه (بدون کانتینر/سرویس جدا)، برای مقیاس هزاران رویداد (نه میلیون‌ها) کاملاً کافیه، فیلتر متادیتا (`category_id`, `format`, `is_paid`, `status`) پشتیبانی می‌شه، و ایندکس وکتور یک artifact قابل بازسازی از SQLite است (از دست رفتن volume آن، data-loss واقعی نیست). Qdrant برای مقیاس بسیار بزرگ‌تر/چندمستأجری مناسب‌تره — به‌عنوان مسیر مهاجرت آینده مستند می‌شه، نه نیاز فعلی.

**مدل embedding:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (چندزبانه، مناسب فارسی، سبک، CPU-friendly، بدون هزینه/تأخیر API خارجی).

---

## 3. مدل داده

### SQLite — جدول‌های اصلی (فیلدهای کلیدی، نه DDL کامل)

| جدول | فیلدهای کلیدی | روابط |
|---|---|---|
| **users** | phone (unique، nullable)، email (unique، nullable)، full_name، role (`user`/`admin`)، status، created_at، last_login_at | organizer = هر کاربری که ≥۱ رویداد داره (بدون نقش جدا) |
| **refresh_tokens** | user_id، token_hash، jti، issued_at، expires_at، revoked_at، replaced_by، user_agent، ip | چرخش (rotation) از طریق `replaced_by` |
| **otp_challenge** | دقیقاً طبق سند: id, user_id, event_id, destination, channel, purpose, otp_hash, created_at, expires_at, attempt_count, max_attempts, status, used_at, last_sent_at, request_ip, provider, provider_message_id, created_by | purpose: `LOGIN` (ورود/ثبت‌نام یکپارچه)، `ADD_CONTACT_CHANNEL`. لینک رویداد خصوصی از طریق OTP نیست (بخش ۸). |
| **categories** | name, slug, parent_id (self-FK، nullable) | دو سطحی: parent → subcategory |
| **tags** | name (unique), slug, usage_count | M:N با `event_tags` |
| **instructors** | name, bio, avatar_url, linked_user_id (nullable), popularity_score (denorm) | M:N با `event_instructors` |
| **events** | organizer_id, title, slug, event_code (unique), description (HTML), description_plain, banner_url, category_id (subcategory), visibility (`PUBLIC`/`PRIVATE`), private_access_token, format (`ONLINE`/`IN_PERSON`/`HYBRID`), venue_address, online_platform_name, status (`DRAFT`/`PUBLISHED`/`CANCELLED`), is_featured, refund_policy, sales_open_at, rating_avg (denorm), rating_count, view_count, published_at | ۱ organizer → N events؛ ۱ event → N sessions/tags/instructors |
| **event_sessions** | event_id, starts_at (UTC), duration_minutes, sequence_order, venue_address override, online_join_url, capacity | هر رویداد حداقل ۱ session (تک‌جلسه‌ای = count==1) |
| **ticket_types** | event_id, name, price, pricing_model (`FREE`/`PAID`/`DONATION`), quantity_total, quantity_sold, is_early_bird | early-bird به‌صورت پویا محاسبه می‌شه، نه استاتیک |
| **orders** | user_id, event_id, status, subtotal/discount/total, discount_code_id (nullable), platform_discount_code_id (nullable), payment_method, payment_status (`NOT_REQUIRED`/`SIMULATED_PAID`/`PENDING`/`PAID`/`FAILED`/`REFUNDED`), completed_at | تک‌نفره طبق تصمیم کاربر |
| **order_items** | order_id, ticket_type_id, session_id, quantity(=1 فعلاً), unit_price, line_total | |
| **registrations** | order_item_id, user_id, event_id, session_id, status (`CONFIRMED`/`CANCELLED`/`CHECKED_IN`), ticket_code (unique), reminder_sent_at (nullable) | مبنای داشبورد شرکت‌کننده‌های برگزارکننده |
| **discount_codes** | event_id (per-event), code, discount_type, value, max_uses, uses_count, valid_from/until, is_active | |
| **platform_discount_codes** | code, discount_type, value, max_uses, uses_count, valid_from/until, is_active, created_by (admin) | کد تخفیف سراسری؛ در چک‌اوت بررسی می‌شه که کد ورودی متعلق به کدام سطح (رویداد یا سایت) است |
| **payments** | order_id, provider (`NONE` فعلاً)، provider_ref, amount, status, raw_payload | آماده‌ی اتصال درگاه واقعی بعداً بدون تغییر مدل |
| **favorites** | user_id, event_id, unique(user_id,event_id) | همان مکانیزم «مارک‌کردن» هم هست (بخش ۱۵) |
| **organizer_follows** / **instructor_follows** | follower_user_id, organizer_id/instructor_id | دو جدول جدا (یکپارچگی FK در SQLite) |
| **event_ratings / instructor_ratings / organizer_ratings / platform_ratings** | user_id, entity_id (به‌جز platform), score(1-5), unique(user_id, entity_id) | ۴ جدول جدا به‌جای یک جدول پلی‌مورفیک (یکپارچگی FK) |
| **event_reviews** | user_id, event_id, registration_id (gate: فقط شرکت‌کننده‌ی واقعی), axis_content_uptodate, axis_instructor_mastery, axis_value_for_price, axis_experience_driven (هرکدام 0-5), overall_computed (میانگین، denorm)، comment_text, status, unique(user_id,event_id) | `overall_computed` منبع `events.rating_avg` است — نظر ۴محوره خودِ امتیاز رویداده |
| **newsletter_subscribers** | email, status, subscribed_at, unsubscribe_token | |
| **notification_outbox** | user_id, event_id, channel, destination, template_key, payload_json, status, attempts, next_attempt_at, provider, provider_message_id | صف مشترک ۳ قالب ثابت |
| **admin_audit_log** | admin_user_id, action, target_type, target_id, reason, metadata_json, ip_address | هر حذف/تعلیق/تغییر ادمین لاگ می‌شه |
| **kpi_daily_snapshot** | date, metric_name, dimensions_json, value | رول‌آپ شبانه از Mongo + SQLite |

### MongoDB — کالکشن‌های آنالیتیکس رفتاری
- `page_views { session_id, user_id?, path, event_id?, referrer, user_agent, ip_hash, ts }`
- `search_queries { session_id, user_id?, query_text, query_type(topic|person), result_count, clicked_result_id?, ts }`
- `funnel_events { session_id, user_id?, event_id?, step(VIEW_EVENT|CLICK_REGISTER|START_CHECKOUT|COMPLETE_ORDER), ts }`
- `click_events { session_id, user_id?, target_type, target_id, ts }`

---

## 4. تصمیم دسته‌بندی موضوعات

**دو سطحی (parent → subcategory، مثل evand)، نه فهرست تخت مثل eseminar.** رویدادها فقط subcategory (برگ) انتخاب می‌کنن؛ دسته‌های والد فقط برای navigation/فیلتر هستن. شروع با ~۸-۱۰ دسته‌ی والد × ۳-۶ زیردسته.

---

## 5. سطح API (بر اساس دامنه)

**Auth/OTP** `/api/v1/auth`: `POST /otp/request`, `POST /otp/verify` (برای purpose=LOGIN، توکن هم صادر می‌کنه)، `POST /otp/resend`, `POST /refresh`, `POST /logout`, `GET /me`

**Events** `/api/v1/events`: `GET /events` (فیلتر: category, tag, price_type, format, timing_status, sort)، `GET /events/{slug}`، `GET /events/code/{event_code}`، `POST /events`، `PATCH|DELETE /events/{id}`، `POST /events/{id}/publish`، `POST /events/{id}/banner`، CRUD `/events/{id}/sessions`، `GET /events/{id}/related`، `GET /events/private/{token}`

**Orders/Tickets**: CRUD `/events/{id}/ticket-types`، `POST /orders`، `POST /orders/{id}/complete`، `GET /orders/{id}`، `GET /me/tickets`، `POST /registrations/{id}/cancel`، `GET /registrations/{id}/calendar-link`، `POST /events/{id}/discount-codes` (برگزارکننده)، `POST /admin/discount-codes` (ادمین، سراسری)، `POST /discount-codes/validate`

**Search** `/api/v1/search`: `GET /search?q=&category=&price_type=&format=&status=`، `GET /search/suggestions`

**Ratings/Reviews**: `POST/GET /events/{id}/reviews`، `POST /ratings {entity_type, entity_id?, score}`، `GET /instructors/{id}`، `GET /organizers/{id}`

**Favorites/Follows**: `POST/DELETE /favorites/{event_id}`، `GET /me/favorites`، `POST/DELETE /follows/organizers/{id}`، `POST/DELETE /follows/instructors/{id}`

**Organizer dashboard** `/api/v1/organizer`: `GET /organizer/events`، `GET /organizer/events/{id}/attendees`، `DELETE /organizer/events/{id}/attendees/{registration_id}`، `GET /organizer/events/{id}/attendees/export`، `GET /organizer/events/{id}/stats`

**Admin** `/api/v1/admin`: `GET/DELETE /admin/events/{id}`، `PATCH /admin/events/{id}/feature`، `GET /admin/users`، `PATCH /admin/users/{id}/suspend`، CRUD `/admin/categories`، `GET /admin/reports/kpis`، `GET /admin/audit-log`

**Newsletter**: `POST /newsletter/subscribe`, `POST /newsletter/unsubscribe`

**Homepage**: `GET /api/v1/home/sections` (هر ۶ بخش در یک فراخوانی، Redis-cached)

---

## 6. Rate Limiting

میان‌افزار عمومی جدا از محدودیت‌های اختصاصی OTP (که دقیقاً طبق سند می‌مونن). استفاده از **`slowapi`** (روی Redis) به‌جای پیاده‌سازی دستی.

- **ناشناس (بر اساس IP):** ~۶۰ درخواست/دقیقه برای خواندن عمومی؛ سخت‌گیرانه‌تر روی endpoint‌های پرهزینه (جستجو ۳۰/دقیقه، ایجاد سفارش ۵/دقیقه، ثبت نظر ۵/دقیقه).
- **احرازشده (بر اساس user_id):** ~۱۲۰/دقیقه عمومی؛ نوشتن سفارش/ثبت‌نام ~۲۰/دقیقه.
- **اقدامات برگزارکننده** (ایجاد/ویرایش رویداد/جلسه/نوع بلیط): ~۲۰/دقیقه.
- **ادمین:** سقف بالا (~۳۰۰/دقیقه)، فقط برای گرفتن اسکریپت‌های رها؛ هر اکشن مستقل از این، در `admin_audit_log` ثبت می‌شه.
- Endpoint‌های OTP از این میان‌افزار عمومی **مستثنا** هستن (محدودیت مخصوص خودشون رو دارن، برای جلوگیری از دوبار محدود شدن).

---

## 7. استراتژی JWT

- **Access token:** ۱۵ دقیقه.
- **Refresh token:** ۳۰ روز، **rotating** — هر فراخوانی `/refresh` توکن جدید صادر و قبلی رو باطل می‌کنه (زنجیره از طریق `replaced_by`). استفاده‌ی مجدد از توکن باطل‌شده = تشخیص سرقت → کل خانواده‌ی توکن باطل می‌شه.
- **ذخیره‌سازی:** refresh token در کوکی **httpOnly, Secure, SameSite=Lax**؛ access token فقط در حافظه (state، نه localStorage) — محافظت در برابر XSS.
- این طراحی الزام «انقضای JWT و اجبار به لاگین مجدد بعد از یک مدت» رو دقیقاً برآورده می‌کنه، در حالی که چرخش refresh این موضوع رو برای کاربر نامرئی نگه می‌داره تا زمانی که خود refresh token منقضی/باطل بشه.

---

## 8. معماری اعلان‌ها (Email/SMS)

یک لایه‌ی provider مشترک، دو مصرف‌کننده: `OTPService` و `NotificationService` جدید، هر دو روی همون اینترفیس‌های `SmsProvider`/`EmailProvider` (پیاده‌سازی: `IPPanelProvider`, `KavenegarProvider`, `BrevoProvider`, `ResendProvider`) که برای OTP طراحی شده.

- `NotificationService` سه قالب ثابت (Jinja2، فارسی) رو رندر می‌کنه: `REGISTRATION_COMPLETE`، `TICKET_PURCHASE_COMPLETE` (شامل جزئیات بلیط + لینک تقویم)، `EVENT_REMINDER_1H` — و به‌جای صدا زدن مستقیم provider، سطر در `notification_outbox` می‌نویسه.
- **دیسپچر** (بخشی از worker اختصاصی) هر ~۱۵ ثانیه صف رو می‌خونه، از طریق provider ارسال می‌کنه، وضعیت رو با retry/backoff به‌روز می‌کنه.
- **لینک Google Calendar**: تابع محض تولید URL (بدون OAuth/API call/ذخیره‌سازی)، از روی `event_sessions` محاسبه می‌شه.
- **یادآوری ۱ساعته**: job زمان‌بند هر ۱ دقیقه `registrations` جوین‌شده با `event_sessions` که `starts_at` در بازه‌ی ۵۹-۶۱ دقیقه‌ی آینده باشه و `reminder_sent_at IS NULL` رو پیدا می‌کنه، سطر outbox می‌سازه (ایمیل+پیامک)، `reminder_sent_at` رو ثبت می‌کنه.
- **لینک رویداد خصوصی** از طریق `NotificationService` ارسال می‌شه، نه OTP.

---

## 9. معماری جستجو

- **جستجوی موضوعی/کلیدواژه‌ای** → embedding با مدل چندزبانه → جستجوی شباهت در ChromaDB (فیلتر متادیتا: category, format, is_paid, status) → گرفتن ردیف‌های زنده از SQLite برای IDهای برگشتی → اعمال فیلتر ساختاریافته و ترتیب نهایی (SQLite تنها منبع حقیقت برای فیلدهای قابل فیلتر باقی می‌مونه).
- **تشخیص جستجوی نام شخص:** قبل از هدایت به جستجوی وکتور، یک تطبیق سبک prefix/LIKE روی نام برگزارکننده‌ها و مدرس‌ها اجرا می‌شه.
- **طراحی UX دوگانه:** یک بخش مجزای «افراد» بالای نتایج (حداکثر ۱-۳ کارت برگزارکننده/مدرس) به‌همراه نتایج رویداد فیلترشده/بوست‌شده حول محتوای آن شخص.
- درخواست‌های خالص فیلتر/مرور (بدون query، فقط دسته/قیمت/فرمت) کاملاً از جستجوی وکتور صرف‌نظر می‌کنن و مستقیم به لیستینگ SQL فیلترشده می‌رن.

---

## 10. بخش‌های الگوریتمی صفحه‌ی اصلی

| بخش | منطق کوئری/رتبه‌بندی |
|---|---|
| برترین وبینارها | `status=PUBLISHED ORDER BY rating_avg DESC` با کف `rating_count >= 3` |
| آخرین وبینارها | `ORDER BY published_at DESC` |
| وبینارهای ویژه | `is_featured=true` (پرچم دستی ادمین)، در صورت کمبود از برترین‌های آینده پر می‌شه |
| مدرس‌های محبوب | `popularity_score` محاسبه‌ی شبانه: `0.5*normalize(follower_count) + 0.5*normalize(rating_avg)` |
| محبوب‌ترین ویدیوها | رویدادهای گذشته با `recording_url` ست‌شده، `ORDER BY view_count DESC` (شمارنده‌ی Redis که دوره‌ای flush می‌شه) |
| برگزارکننده‌های محبوب | همان الگوی popularity_score از `organizer_follows` + امتیاز + تعداد رویداد |

همه از طریق یک `GET /api/v1/home/sections`، هرکدام در Redis کش می‌شن (TTL ۵-۱۰ دقیقه).

---

## 11. آنالیتیکس/KPI

**فهرست KPI:** نرخ تبدیل قیف (VIEW→CLICK→CHECKOUT→COMPLETE)، نرخ ثبت‌نام، دسته‌های محبوب، کلیدواژه‌های پرجستجو + **جستجوهای بی‌نتیجه**، نقاط ریزش چک‌اوت، عملکرد برگزارکننده، نرخ تبدیل خبرنامه، سلامت قیف OTP، DAU/WAU تقریبی.

**ثبت:** یک beacon سبک فرانت (`POST /api/v1/track`) بدون بلاک UI به کالکشن‌های Mongo می‌نویسه.

**تجمیع:** job شبانه در worker، pipeline‌های Mongo + کوئری‌های SQLite رو اجرا و در `kpi_daily_snapshot` (SQLite) می‌نویسه.

**سطح گزارش ادمین:** `GET /api/v1/admin/reports/kpis?range=`.

---

## 12. معماری فرانت‌اند (Next.js)

- **استک:** Next.js (App Router) + shadcn/ui + Tailwind. صفحات رویداد (`/events/[slug]`) و صفحات دسته‌بندی به‌صورت SSR/ISR برای SEO؛ صفحات پشت لاگین (داشبورد، پنل ادمین، سبد خرید) می‌تونن CSR باشن.
- **فونت:** Kalameh (محلی، `next/font/local`، `frontend/src/fonts/kalameh.ts`) — همه‌ی وزن‌ها (Thin تا Black).
- **State:** TanStack Query برای state سرور + Zustand برای state خالص کلاینت.
- **RTL/فارسی:** `dir="rtl"` + `lang="fa"` روی ریشه، کلاس‌های منطقی Tailwind (`ps-*`/`pe-*`). تاریخ: `dayjs` + پلاگین جلالی برای نمایش، ذخیره/انتقال UTC/میلادی.
- **ریسپانسیو بودن (الزامی، طبق درخواست کاربر):** تمام صفحات و کامپوننت‌ها باید mobile-first و کاملاً ریسپانسیو باشن (موبایل/تبلت/دسکتاپ). از breakpointهای استاندارد Tailwind (`sm/md/lg/xl`) و کلاس‌های flex/grid ریسپانسیو استفاده می‌شه؛ هیچ عرض/ارتفاع ثابتی که در موبایل بشکنه مجاز نیست. هر صفحه‌ی جدید باید حداقل در دو breakpoint (موبایل و دسکتاپ) بررسی بصری بشه.
- **الگوی مقاومت در برابر قطع اتصال:** `useNetworkStatus` ترکیب رویدادهای `online`/`offline` مرورگر + پینگ دوره‌ای سبک `/api/v1/health`؛ اگر آفلاین در حالی که لاگین → پس از اتصال مجدد refresh خاموش توکن، شکست → ریدایرکت به ورود OTP؛ اگر آفلاین بدون لاگین → اسکلت تمام‌صفحه تا اتصال واقعی برقرار بشه.

---

## 13. ساختار پوشه‌ی مونوریپو

```
RoyaEvent/
  backend/app/{api,models,schemas,services,providers,core,workers,search,db}/
  backend/tests/{unit,integration}/
  frontend/src/{app,components,fonts,lib,hooks,store}/
  infra/{docker-compose.yml,nginx,prometheus,grafana,loki}/
  data/{eseminar.tv,evand.com}/analysis.md
  docs/{architecture.md,event_otp_email_sms_plan_fa.md,adrs}/
  .github/workflows/
```

---

## 14. نقشه‌ی راه فازبندی‌شده

هر فاز با چند commit کوچک و مرتب روی GitHub ثبت می‌شه.

- **فاز ۰ — Scaffolding و مستندات.** ✅ — ساختار backend/frontend، docker-compose، تحلیل رقبا، مستندات.
- **فاز ۱ — Auth/OTP + کاربران.** ✅ — جداول `users`/`otp_challenge`/`refresh_tokens` (Alembic)، `OTPService` (تولید/هش/rate-limit/انقضا/قفل)، provider abstraction (Console/IPPanel/Kavenegar/Brevo/Resend)، `AuthService` (JWT access+refresh چرخشی با تشخیص سرقت)، endpoint‌های `/auth/otp/*`, `/auth/refresh`, `/auth/logout`, `/auth/me`، صفحه‌ی ورود OTP در فرانت، ۵۵ تست (unit+integration) پاس.
- **فاز ۲ — CRUD رویداد + دسته‌بندی/تگ/جلسه + آپلود بنر امن روی MinIO.** ✅ — مدل‌های `Category`(دوسطحی)/`Tag`/`Instructor`/`Event`/`EventSession` + Alembic + seed ۱۰ دسته‌ی والد؛ `validate_and_reencode_image()` (بخش ۱۶، magic-byte + رد SVG + re-encode اجباری)؛ `event_service` (event_code/slug یکتا، انتشار، لغو)؛ events router کامل (شامل رفع نشتی امنیتی DRAFT از endpointهای عمومی)؛ میان‌افزار rate-limit عمومی slowapi؛ فرم چندبخشی ایجاد رویداد + آپلود بنر + انتشار در فرانت؛ صفحه‌ی عمومی جزئیات رویداد SSR با JSON-LD schema.org/Event و تاریخ شمسی بومی (Intl fa-IR-u-ca-persian)؛ لیستینگ عمومی + «رویدادهای من»؛ ۱۰۱ تست (unit+integration) پاس، تأیید بصری end-to-end با سرور واقعی.
- **فاز ۳ — بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن.**
- **فاز ۴ — جستجو + صفحه‌ی اصلی.**
- **فاز ۵ — پنل ادمین.**
- **فاز ۶ — اعلان‌ها + زمان‌بند + لینک تقویم.**
- **فاز ۷ — امتیاز/نظر/علاقه‌مندی تکمیلی.**
- **فاز ۸ — آنالیتیکس/KPI.**
- **فاز ۹ — استک مانیتورینگ.**
- **فاز ۱۰ — تقویت تست + مقاومت/RTL.**
- **فاز ۱۱ — آماده‌سازی دیپلوی VPS.**

جزئیات کامل هر فاز (خروجی/معیار تکمیل) در تاریخچه‌ی پلن پروژه موجوده؛ خلاصه‌ی بالا برای مرجع سریع کافیه.

---

## 15. تصمیمات نهایی روی نکات مبهم اولیه

1. علاقه‌مندی‌ها (Favorites) و «مارک‌کردن» یک مکانیزم واحدند.
2. نظر ۴محوره منبع امتیاز ستاره‌ای رویداده؛ امتیاز مدرس/برگزارکننده/سایت یک ضربه‌ی ساده‌ی ۱-۵ ستاره جداست.
3. بدون گیت تأیید برای ایجاد رویداد — فقط rate limit.
4. Next.js با SSR/Prerender برای صفحات عمومی؛ صفحات پشت لاگین CSR.
5. اعتبارسنجی موبایل ایرانی: regex فرمت + پیش‌شماره‌ی اپراتور؛ ایمیل: regex + بررسی اختیاری MX.
6. هر سفارش تک‌نفره.
7. کد تخفیف در دو سطح (رویداد + سایت/ادمین).
8. امتیازها در ۴ جدول جدا (نه پلی‌مورفیک) — یکپارچگی FK در SQLite.
9. SQLite با WAL mode از روز اول.
10. هزینه‌ی پیامک غیر-OTP باید از ابتدا در بودجه لحاظ بشه؛ opt-out آینده ممکنه.
11. لینک رویداد خصوصی از طریق NotificationService، نه OTP.

## 16. امنیت آپلود فایل (بنر رویداد و سایر آپلودها)

آپلود بنر (و هر فایل کاربر دیگری) باید طوری طراحی بشه که فایل مخرب (ویروس/تروجان/پی‌لود پنهان‌شده با steganography در یک تصویر به‌ظاهر سالم) نتونه امنیت سایت رو به خطر بندازه. در فاز ۲ این خط‌مشی‌ها اجرا می‌شه:

- اعتبارسنجی نوع فایل بر اساس **magic bytes**، نه پسوند/`Content-Type` ارسالی از کلاینت.
- محدود به فرمت‌های راستری امن (JPEG/PNG/WebP) — **SVG رد می‌شه**.
- **Re-encode اجباری روی سرور** (Pillow): decode و دوباره encode به یک فایل تصویری تازه — بیشتر payloadهای پنهان‌شده (steganography، الحاقی انتهای فایل، EXIF مخرب) از بین می‌ره چون فقط پیکسل‌های واقعی باقی می‌مونن.
- حذف کامل متادیتا (EXIF/ICC) هنگام re-encode.
- محدودیت اندازه/ابعاد فایل قبل از پردازش (جلوگیری از decompression-bomb).
- نام‌گذاری تصادفی (UUID) در MinIO؛ فایل هیچ‌وقت در مسیر قابل‌اجرا سرو نمی‌شه.
- (اختیاری، production) اسکن ClamAV به‌عنوان لایه‌ی دفاعی اضافه — در راهنمای دیپلوی فاز ۱۱ مستند می‌شه.

منطق مشترک در `backend/app/services/` (`validate_and_reencode_image()`) پیاده‌سازی می‌شه تا هم بنر رویداد و هم هر آپلود تصویری دیگری از همون مسیر امن عبور کنن.

## 17. نکته‌ی لایسنس فونت Kalameh

فونت Kalameh (پوشه‌ی `/font` در ریشه‌ی ریپو، `git-ignore` شده) یک فونت تجاری/مالکیتی (fontiran.com) است. فایل `FontLicense.txt` همراهش نشون می‌ده کد ۶رقمی لایسنس وب هنوز درج نشده. طبق تصمیم صریح کاربر، فایل‌های وب‌فونت (`frontend/src/fonts/kalameh/*.woff2`) در ریپوی عمومی GitHub کامیت و منتشر می‌شن؛ این یک تصمیم آگاهانه‌ی کاربره، نه یک oversight — قبل از استفاده‌ی تجاری واقعی، تهیه‌ی لایسنس وب معتبر از fontiran.com توصیه می‌شه.
