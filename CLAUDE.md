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
| ۴ | جستجو (ChromaDB) + صفحه‌ی اصلی | ✅ [`specs/spec4.md`](specs/spec4.md) |
| ۵ | پنل ادمین | ✅ [`specs/spec5.md`](specs/spec5.md) |
| ۶ | اعلان‌ها + زمان‌بند + لینک تقویم | ✅ [`specs/spec6.md`](specs/spec6.md) |
| ۷ | امتیاز/نظر ۴محوره رویداد + امتیاز ساده مدرس/برگزارکننده/سایت | ✅ [`specs/spec7.md`](specs/spec7.md) |
| ۸ | آنالیتیکس/KPI | ⏳ شروع نشده |
| ۹ | استک مانیتورینگ | ⏳ شروع نشده |
| ۱۰ | تقویت تست + مقاومت آفلاین/RTL | ⏳ شروع نشده |
| ۱۱ | آماده‌سازی دیپلوی VPS (TLS/HTTPS اجباری — نگاه کن به بخش تصمیمات) | ⏳ باقی فاز نشده؛ بخش TLS/Nginx/Docker زودتر و مستقل انجام شد، نگاه کن به `docs/deployment_tls.md` و `specs/spec3.md` |

بک‌اند در مجموع الان **۲۸۷ تست** دارد (unit+integration)، همه پاس، `ruff check .` تمیز. فرانت `npm run build` و `npx eslint src --max-warnings=0` هر دو تمیز.

## استک فنی (تصمیم قطعی، تغییر نده مگر کاربر بخواد)

| لایه | فناوری |
|---|---|
| فرانت‌اند | Next.js 16 (App Router) + shadcn/ui (بر پایه‌ی Base UI، نه Radix) + Tailwind v4، RTL/فارسی |
| بک‌اند | FastAPI (Python 3.12) |
| DB اصلی | SQLite (WAL mode)، از طریق SQLAlchemy 2.0 + Alembic |
| آنالیتیکس رفتاری | MongoDB (فاز ۸، هنوز کدی نیست) |
| کش/Rate-limit | Redis |
| فایل/بنر/ویدیو | S3-compatible Object Storage — **ArvanCloud Object Storage** فعال (production/dev اشتراکی، کلید در `.env`، هرگز commit نمی‌شه)؛ **MinIO خودمیزبان** (`infra/docker-compose.yml`) به‌عنوان سناریوی جایگزین همیشه در دسترس می‌مونه — کد (`app/core/storage.py`) با `minio-py` صحبت می‌کنه که با هر دو کار می‌کنه، سوییچ فقط تغییر ۴-۵ متغیر در `.env` است، بدون تغییر کد |
| جستجوی محتوایی | ChromaDB embedded (`backend/app/search/`) + `sentence-transformers` (مدل `paraphrase-multilingual-MiniLM-L12-v2`، چندزبانه) — فعال از فاز ۴. **موقع نصب local/Docker از این پس، حتماً اول `pip install torch --index-url https://download.pytorch.org/whl/cpu` رو جدا بزن**، بعد `pip install -r requirements.txt` — وگرنه نصب `sentence-transformers` سراغ wheel غول‌پیکر CUDA torch می‌ره |
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
    api/v1/routers/   # auth.py, events.py, tickets.py, orders.py, social.py, organizer.py (داشبورد خصوصی)،
                      # organizers.py (پروفایل عمومی، پیچیده نکن با organizer.py)، instructors.py, search.py, home.py, admin.py، ratings.py
    api/deps.py        # get_db, get_current_user, get_current_user_optional, get_current_admin_user, get_redis, get_sms/email_provider, get_client_ip
    core/               # config, security (JWT+OTP hash), rate_limit (OTP), rate_limit_middleware (عمومی/slowapi)
                        # redis_client, storage (MinIO), slug, validators, calendar (لینک گوگل‌کلندر)
                        # permissions (require_event_owner, require_complete_profile)، persian_date (UTC→جلالی تهران، برای متن پیامک/ایمیل)
    db/                 # session.py (engine/Base/get_db)، migrations/ (Alembic)، seed_categories.py
    models/             # User, OTPChallenge, RefreshToken, Category, Tag, Instructor, Event, EventSession,
                        # TicketType, DiscountCode, PlatformDiscountCode, Order, OrderItem, Payment, Registration,
                        # Favorite, OrganizerFollow, InstructorFollow, AdminAuditLog, NotificationOutbox,
                        # EventReview (نظر ۴محوره)، InstructorRating/OrganizerRating/PlatformRating (امتیاز ساده)
    providers/sms|email/ # base + console(dev) + ippanel/kavenegar/brevo/resend
    schemas/            # auth.py, event.py, ticket.py, order.py, social.py, organizer.py (AttendeeOut + OrganizerProfileOut)،
                        # instructor.py, search.py, home.py, admin.py (Pydantic)، review.py, rating.py
    services/           # otp_service, auth_service, event_service (+event_query/to_list_item_out عمومی)،
                        # image_service, video_service, ticket_service, discount_service, order_service,
                        # social_service, instructor_service, organizer_service (پروفایل عمومی)،
                        # search_service (جستجوی دوگانه: افراد+رویداد)، home_service (بخش‌های صفحه‌ی اصلی، Redis-cached)،
                        # admin_service (soft-delete رویداد، تعلیق کاربر، CRUD دسته‌بندی، لاگ اقدامات، hide/unhide نظر)،
                        # notification_service (enqueue صف اعلان)، notification_templates (رندر Jinja2 هر قالب×کانال)،
                        # review_service (نظر ۴محوره رویداد، gate ثبت‌نام+زمان جلسه)، rating_service (امتیاز زنده‌محاسبه‌ی مدرس/برگزارکننده/سایت)
    search/             # chroma_client.py, embeddings.py, indexer.py (sync_event_index)، reindex.py (بک‌فیل دستی)
    workers/            # scheduler.py — پردازه‌ی جدا (python -m app.workers.scheduler)، دیسپچر صف اعلان + اسکنر یادآوری ۱ساعته
  backend/tests/unit|integration/   # pytest، fakeredis، بدون نیاز به Redis واقعی (+ test_search_api.py: embedding/Chroma قلابی)
  frontend/src/
    app/
      (auth)/login/page.tsx        # ورود OTP (client)
      (organizer)/events/create/   # فرم ایجاد رویداد (client)
      (organizer)/events/mine/     # لیست رویدادهای من (client)
      (organizer)/organizer/events/[id]/attendees/  # داشبورد شرکت‌کنندگان + export CSV (client)
      (organizer)/organizer/events/[id]/checkin/    # چک‌این حضوری — اسکنر دوربین (html5-qrcode) + ورود دستی کد (client)
      (organizer)/organizer/events/[id]/media/      # ویرایش بنر/کلیپ بعد از ایجاد یا حتی بعد از انتشار (client)
      (organizer)/organizer/events/[id]/tickets/    # مدیریت انواع بلیط رویداد — افزودن/لیست (client)
      (organizer)/organizer/events/[id]/edit/       # ویرایش عنوان/توضیحات/دسته/جلسه‌ها و... — مالک رویداد یا ادمین (client)
      events/page.tsx              # لیستینگ عمومی (SSR/dynamic + فیلتر دسته‌بندی/نوع‌برگزاری با searchParams)
      events/[slug]/page.tsx       # جزئیات رویداد عمومی (SSR/dynamic + JSON-LD + چک‌اوت/فوتر چسبان/favorite/follow)
      tickets/page.tsx             # «بلیط‌های من» (client)
      favorites/page.tsx           # «علاقه‌مندی‌های من» (client)
      follows/page.tsx             # «دنبال‌کردن‌های من» — برگزارکننده‌ها + مدرس‌ها با اسم (client)
      instructors/[id]/page.tsx    # پروفایل عمومی مدرس — بیوگرافی/آواتار/رویدادهای منتشرشده (SSR/dynamic)
      organizers/[id]/page.tsx     # پروفایل عمومی برگزارکننده — مشابه instructors/[id] (SSR/dynamic)
      profile/page.tsx             # فرم نام + آپلود آواتار کاربر (client)
      search/page.tsx              # نتایج جستجو — بخش «افراد» + «رویدادها» (SSR/dynamic)
      admin/page.tsx                # پنل ادمین — تب رویدادها/کاربران/دسته‌بندی‌ها/لاگ اقدامات (client، فقط role===admin)
      page.tsx                     # خانه (async Server Component، یک fetch به /home/sections)
    components/EventCard.tsx       # کارت رویداد (Server Component)
    components/EventCarousel.tsx   # کاروسل بخش‌های صفحه‌ی اصلی — فلش‌ها + «مشاهده همه» (client)
    components/BackToTopButton.tsx # دکمه‌ی شناور «برو بالا» بعد از اسکرول، در layout ریشه (client)
    components/EventsFilter.tsx    # Select دسته‌بندی/نوع‌برگزاری برای events/page.tsx، sync با URL
    components/TicketCheckout.tsx, StickyTicketFooter.tsx, FavoriteButton.tsx, FollowOrganizerButton.tsx  # فاز ۳ (client)
    components/FollowInstructorButton.tsx # دکمه‌ی دنبال‌کردن مدرس، کپی الگوی FollowOrganizerButton (client)
    components/InstantRegisterModal.tsx, InstantRegisterButton.tsx # ثبت‌نام فوری (OTP+ثبت‌نام یک‌جا از روی کارت رویداد)
    components/RoyaEventLogo.tsx   # لوگوی متنی برند (سبز/سفید/قرمز)
    components/RoyaEventLoader.tsx # اسپلش‌اسکرین، وصل به app/loading.tsx (Suspense خودکار نکست‌جس)
    components/SiteHeader.tsx      # هدر مشترک (لوگو+تگ‌لاین+نوار جستجو+ناوبری+آواتار کنار پروفایل)، در layout ریشه، client
    components/SiteFooter.tsx      # فوتر مشترک — کپی‌رایت با سال شمسی + لوگوی کوچک، در layout ریشه
    components/OnboardingTour.tsx  # اجرای خودکار تور بار اول (driver.js)، بدون UI خودش
    components/SessionBootstrap.tsx # بازیابی خودکار access token با کوکی refresh موقع لود صفحه، بدون UI
    components/CompleteProfilePrompt.tsx # فرم تکمیل نام، وقتی require_complete_profile خطای ۴۲۲ بده (داخل TicketCheckout/create-event)
    components/NewsletterSignup.tsx # کارت خبرنامه (فقط اعتبارسنجی/localStorage، بدون بک‌اند واقعی)
    components/JalaliDateTimePicker.tsx # تاریخ‌ساعت شمسی (react-multi-date-picker) برای فیلدهای جلسه
    components/StarRating.tsx      # نمایش/دریافت امتیاز ۱-۵ ستاره، همیشه dir="ltr" داخلی — مشترک بین نظر رویداد و امتیاز مدرس/برگزارکننده
    components/EventReviews.tsx    # فرم نظر ۴محوره + لیست نظرهای رویداد، در events/[slug]
    components/RateEntityWidget.tsx # ویجت امتیازدهی ستاره‌ای مشترک مدرس/برگزارکننده (الگوی FollowInstructorButton)
    components/TicketQrCode.tsx    # QR بلیط («بلیط‌های من») — لینک /organizer/events/{id}/checkin?code=... رو کد می‌کنه، نه متن خام کد
    components/ui/                 # shadcn primitives (+ textarea, select, combobox, progress, checkbox, dialog)
    lib/
      api-client.ts    # fetch wrapper سمت کلاینت، credentials:include، پشتیبانی FormData،
                        # refreshAccessToken() (guard تک‌پرواز رفرش توکن) + retry خودکار روی ۴۰۱، authApi (+uploadAvatar)
      events-api.ts     # انواع TS + توابع کلاینت events/categories (نیاز به accessToken)
      events-server.ts  # فراخوانی سمت سرور برای RSC (cache:"no-store"، بدون کوکی)
      instructors-api.ts, instructors-server.ts  # کلاینت + SSR برای /instructors (مشابه events-api/events-server)
      organizers-api.ts, organizers-server.ts    # کلاینت + SSR برای /organizers (پروفایل عمومی، نه داشبورد organizer-api.ts)
      search-api.ts, search-server.ts  # کلاینت + SSR برای /search
      admin-api.ts        # کلاینت برای /admin/* (نیاز به accessToken با role=admin)
      home-server.ts     # SSR برای /home/sections (فقط سرور — صفحه‌ی اصلی چیزی سمت کلاینت لازم نداره)
      tickets-api.ts, orders-api.ts, social-api.ts, organizer-api.ts  # فاز ۳ (social-api.ts: +myFollowsDetail)
      reviews-api.ts, ratings-api.ts  # فاز ۷ — نظر ۴محوره رویداد + امتیاز ساده مدرس/برگزارکننده/سایت
      date.ts            # formatJalali* — Intl بومی fa-IR-u-ca-persian، بدون کتابخانه‌ی جانبی
    store/auth-store.ts  # Zustand، accessToken فقط در حافظه + user (UserOut، برای نمایش‌های سبک مثل آواتار هدر)
    fonts/kalameh.ts
  backend/Dockerfile, frontend/Dockerfile   # production images (نگاه کن به docs/deployment_tls.md)
  infra/docker-compose.yml        # dev: redis, mongo, minio, loki, prometheus, grafana
  infra/docker-compose.prod.yml   # production: + nginx (TLS)، certbot، backend، frontend
  infra/nginx/conf.d/royaevent.conf, infra/renew-certs.sh   # پیکربندی TLS + اسکریپت تمدید گواهی (کرون هاست)
  data/eseminar.tv/, data/evand.com/   # تحلیل رقبا
  docs/architecture.md        # پلن کامل معماری (مرجع اصلی طراحی)
  docs/event_otp_email_sms_plan_fa.md  # سند اولیه‌ی OTP (کاربر داده، مرجع دقیق مکانیزم OTP)
  docs/deployment_tls.md      # راهنمای دیپلوی production + TLS اجباری با Nginx/Let's Encrypt
  specs/                       # تاریخچه‌ی اجرای فازها — یک specN.md به‌ازای هر فاز (نگاه کن به specs/README.md)
```

## کارهای درخواستی در صف (خارج از نقشه‌ی راه اصلی، هنوز شروع نشده)

کاربر این‌ها رو مستقیم درخواست داده؛ باید قبل از فاز ۴ یا در کنارش انجام بشن:

1. ~~آپلود کلیپ کوتاه تبلیغاتی رویداد~~ ✅ **انجام شد** — `promo_video_url` روی `events`، `app/services/video_service.py` (اعتبارسنجی magic-byte MP4/WebM، سقف ۳۰MB، بدون transcode)، endpoint `POST /events/{id}/promo-video`، آپلود پیشرفت‌دار (XMLHttpRequest + درصد) در فرم ایجاد رویداد، پخش‌کننده در صفحه‌ی رویداد (video با poster=banner اگه هر دو باشن). جزئیات کامل در `specs/spec3.md`.
2. ~~تور آموزشی سایت~~ ✅ **انجام شد** — با `driver.js`. `lib/onboarding-tour.ts` (تعریف مراحل + استارت)، `components/OnboardingTour.tsx` (فقط اجرای خودکار بار اول، چک با `localStorage`، بدون رندر UI)، دکمه‌ی «راهنمای سایت» (آیکون `CircleHelp`) در `SiteHeader` برای تکرار دستی هروقت کاربر خواست. مراحل تور روی `id`های `tour-logo/tour-events/tour-create/tour-mine/tour-tickets/tour-login` در هدر. RTL polish برای popover در `globals.css` (کلاس `.roya-tour-popover`). جزئیات کامل در `specs/spec3.md`.
3. ~~TLS/HTTPS اجباری در production~~ ✅ **انجام شد** — `backend/Dockerfile`+`frontend/Dockerfile` (production images، تست build شد و موفق بود)، `infra/docker-compose.prod.yml` (nginx+certbot+backend+frontend+redis+mongo+minio اختیاری)، `infra/nginx/conf.d/royaevent.conf` (ریدایرکت اجباری HTTP→HTTPS + HSTS)، `infra/renew-certs.sh` (تمدید گواهی از کرون هاست). راهنمای کامل قدم‌به‌قدم در `docs/deployment_tls.md`. جزئیات/تصمیمات فنی (چرا certbot سرویس همیشه‌روشن نیست، مشکل apt-get و راه‌حلش) در `specs/spec3.md`.
4. ~~لیست «دنبال‌کردن‌های من» + مدرس‌های محبوب/وبینارهای محبوب در صفحه‌ی اصلی + آپلود عکس پروفایل~~ ✅ **انجام شد** — سیستم «مدرس» (که فقط یه جدول خالی بود) از پایه ساخته شد: get-or-create با اسم موقع ایجاد رویداد، `GET /instructors`، `GET /instructors/{id}` (+رویدادهاش)، صفحه‌ی عمومی `instructors/[id]`. `GET /me/follows/details` (نسخه‌ی enrich‌شده‌ی `/me/follows`) + صفحه‌ی `follows/`. `avatar_url` روی `User` + `POST /auth/me/avatar` + صفحه‌ی `profile/`. `GET /events?sort=popular` (بر اساس `view_count`، چون فاز ۷ امتیازدهی هنوز نیست). جزئیات کامل در `specs/spec3.md`.
5. ~~ثبت‌نام فوری~~ ✅ **انجام شد** — `is_instant_registration` روی `Event` (جدا از پولی/رایگان/حمایتی بودن بلیط). `InstantRegisterModal.tsx` + `InstantRegisterButton.tsx` (داخل `EventCard`، با `stopPropagation`): اگه لاگین نباشه اول OTP می‌گیره، اگه لاگین باشه یه مرحله‌ی «تأیید» ساده قبل از ثبت‌نام واقعی نشون می‌ده (نه ثبت‌نام کاملاً بی‌اطلاع کاربر). فقط رویدادهای instant برچسب «فوری» می‌گیرن. جزئیات کامل و دام‌های react-hooks/set-state-in-effect که حین ساختش کشف شد در `specs/spec4.md`.
6. ~~کلیک روی اسم برگزارکننده/مدرس باید به صفحه‌ی رویدادهاش بره~~ ✅ **انجام شد** — مدرس از قبل کار می‌کرد (فاز ۳ addendum)؛ برگزارکننده جدید بود: `GET /organizers/{id}` + صفحه‌ی `organizers/[id]` (مشابه صفحه‌ی مدرس)، اسم برگزارکننده تو `/follows` و صفحه‌ی جزئیات رویداد حالا لینکه.
7. ~~چک‌این حضوری با QR (Phase 2 سند `docs/RoyaEvent_Registration_Ticket_Access_Attendance.md`)~~ ✅ **انجام شد** — `Registration.checked_in_at`/`checked_in_by_user_id` (بدون FK رسمی، فقط audit)، `order_service.check_in_registration`، `POST /organizer/events/{id}/checkin`. فرانت: `TicketQrCode.tsx` (QR بلیط، لینک کامل `/organizer/events/{id}/checkin?code=...` رو کد می‌کنه نه متن خام کد، تا با دوربین عادی گوشی هم کار کنه) + صفحه‌ی `organizer/events/[id]/checkin` (اسکنر دوربین درون‌اپ با `html5-qrcode` + فرم ورود دستی، `?code=` از QR فقط مقدار اولیه‌ی فرمه، هنوز یک تپ تأیید لازمه). دامنه‌ی این فاز عمداً فقط چک‌این حضوری بود؛ Access امن آنلاین/Attendance چندسطحی/Certificate سند از بهبودهای آینده‌ان.
8. **پذیرش قوانین/شرایط استفاده** ⏳ **در صف، منتظر متن از کاربر** — قبل از ایجاد رویداد یا خرید بلیط باید کاربر قوانین سایت رو تأیید کرده باشه؛ احتمالاً با همون الگوی `require_complete_profile` (گارد قبل از `POST /events`/`POST /orders`) پیاده می‌شه.

## قراردادهای API

- Base path: `/api/v1` (از `settings.api_v1_prefix`)
- Auth: `Authorization: Bearer <access_token>` برای access token (در حافظه‌ی فرانت، نه localStorage)؛ refresh token در کوکی httpOnly به اسم `refresh_token` (مسیر `/`)
- خطاها: `HTTPException` با پیام فارسی؛ برای OTP/Auth عمداً پیام‌های عمومی (بدون افشای این‌که کاربر/OTP وجود داره یا نه)
- همه‌ی مدل‌های زمانی در DB **naive UTC** هستن (نه timezone-aware) — SQLite مقایسه‌ی aware/naive رو با TypeError رد می‌کنه؛ همیشه از `app.models.base.utcnow()` استفاده کن، نه `datetime.now(timezone.utc)` مستقیم
- Provider abstraction: کد سرویس هرگز مستقیم IPPanel/Kavenegar/Brevo/Resend صدا نمی‌زنه؛ از `get_sms_provider()`/`get_email_provider()` (factory، بر اساس `.env`) رد می‌شه. بدون API key، خودکار می‌ره روی `ConsoleProvider` (فقط لاگ، برای dev/test)
- **قاعده‌ی دائمی (از باگ امنیتی فاز ۲):** بعد از نوشتن هر endpoint عمومی/بدون احراز هویت که رویداد یا هر رکورد دارای وضعیت (status) برمی‌گردونه، از خودت بپرس «آیا وضعیت DRAFT/CANCELLED هم از این مسیر قابل دیدنه؟» — جزئیات حادثه در `specs/spec2.md`.
- **تکمیل پروفایل اجباری:** `PATCH /auth/me` (`{full_name}`) نام کاربر رو آپدیت می‌کنه. `core/permissions.py: require_complete_profile(user)` قبل از `POST /events` و `POST /orders` صدا زده می‌شه و اگه `full_name` خالی باشه ۴۲۲ با پیام «برای این کار باید ابتدا نام و نام خانوادگی خود را تکمیل کنید» برمی‌گردونه. فرانت این پیام دقیق رو با `isIncompleteProfileError()` (`lib/api-client.ts`) تشخیص می‌ده و به‌جای نمایش خطای خام، `CompleteProfilePrompt` رو نشون می‌ده. هر endpoint نوشتنی جدیدی که یک کاربر OTP-only (بدون نام) می‌تونه بهش برسه، باید همین گارد رو صدا بزنه.
- **آواتار کاربر:** `POST /auth/me/avatar` — همون `validate_and_reencode_image` امن بنر رویداد رو re-use می‌کنه، فقط `storage.upload_avatar_image()` جدا (namespace `avatars/{user_id}/...` تو MinIO/ArvanCloud).
- **مدرس (get-or-create با اسم):** `instructor_names` روی `EventCreateIn`/`EventUpdateIn`، دقیقاً مثل `tag_names` — رشته‌ی دقیقاً یکسان = همون رکورد، وگرنه رکورد جدید (`event_service._get_or_create_instructors`). `GET /instructors` (مرتب بر اساس follower_count زنده)، `GET /instructors/{id}` (بیوگرافی+رویدادهای منتشرشده+`is_following`). برای auth اختیاری (کاربر لاگین‌کرده یا نه، رفتار endpoint کمی فرق می‌کنه) از `deps.py: get_current_user_optional` استفاده کن، نه `get_current_user` اجباری.
- **محبوبیت (MVP):** `GET /events?sort=popular` بر اساس `view_count` (`sort=top_rated` جداست، بر اساس `rating_avg`— نگاه کن به بند نظر/امتیاز پایین). همین‌طور `GET /instructors` بر اساس `follower_count` زنده، نه رول‌آپ شبانه‌ی `popularity_score` (که در `architecture.md` برای آینده/مقیاس بزرگ‌تر پیش‌بینی شده).
- **جستجو:** `GET /search?q=&category_id=&format=` — همیشه هم `search_people` (prefix match مدرس/برگزارکننده) هم `search_events` (embedding + ChromaDB) رو با هم اجرا می‌کنه، نه either/or. هر رویدادی که PUBLISHED+PUBLIC می‌شه (یا اسم/توضیحاتش عوض می‌شه) باید `app/search/indexer.py: sync_event_index(event)` صداش بزنه — این قلاب از قبل تو `event_service.py: publish_event/update_event/cancel_event` هست، برای هر تابع جدیدی که وضعیت/محتوای رویداد رو عوض می‌کنه هم باید صدا زده بشه. رویدادهای منتشرشده‌ی قبل از فاز ۴ باید یک‌بار دستی با `python -m app.search.reindex` بک‌فیل بشن.
- **صفحه‌ی اصلی:** همه‌چیز از یک `GET /home/sections` میاد (Redis-cached، TTL ۵ دقیقه، کلید `home:sections`) — هیچ‌وقت مستقیم چند تا endpoint جدا برای بخش‌های صفحه‌ی اصلی صدا نزن، همه باید از `home_service.py` عبور کنن تا کش یک‌جا کار کنه. بخش «ویژه» تا وقتی پنل ادمین (فاز ۵) امکان ست‌کردن دستی `is_featured` رو نداره، fallback‌ش بر اساس محبوبیت واقعی برگزارکننده (تعداد دنبال‌کننده) انتخاب می‌کنه، **نه** صرفاً جدیدترین‌ها — وگرنه این بخش با «آخرین وبینارها» یکی به نظر می‌رسه (بازخورد مستقیم کاربر).
- **پروفایل عمومی برگزارکننده/مدرس:** `GET /organizers/{id}` و `GET /instructors/{id}` — هر جا اسم برگزارکننده یا مدرس نمایش داده می‌شه (کارت رویداد، صفحه‌ی جزئیات، `/follows`)، باید لینک به این صفحات باشه، نه متن ساده.
- **ثبت‌نام فوری:** `is_instant_registration` روی `Event`، مستقل از `pricing_model` بلیط. فقط برای نشون‌دادن UI متفاوت (modal به‌جای رفتن به صفحه‌ی جزئیات) استفاده می‌شه، منطق سفارش/بلیط پشت صحنه دقیقاً همون `POST /orders` + `POST /orders/{id}/complete` قبلیه.
- **پنل ادمین:** همه‌چیز زیر `/admin`، گارد `get_current_admin_user`. هر endpoint نوشتنی جدید زیر `/admin` باید `admin_service.log_action(...)` رو صدا بزنه، وگرنه لاگ اقدامات ناقصه. **تعلیق کاربر (`UserStatus.SUSPENDED`) باید تو سه جای auth flow چک بشه**، نه فقط یکی: `verify_otp` (رد لاگین جدید با پیام روشن)، `AuthService.get_user_from_access_token` (باطل‌کردن access tokenهای از قبل صادرشده)، و `AuthService.refresh` (جلوگیری از گرفتن access token تازه با refresh token چرخشی قدیمی) — این سه جدان چون مسیرهای متفاوتی برای رسیدن کاربر تعلیق‌شده به سرورن. `GET /admin/notifications` (صف `NotificationOutbox`) استثناست — کاملاً فقط-خواندنیه، `log_action` نمی‌خواد چون هیچ‌چیزی رو تغییر نمی‌ده.
- **چک‌این حضوری:** `POST /organizer/events/{id}/checkin` (بدنه `{ticket_code}`) — فقط مالک رویداد/ادمین. `order_service.check_in_registration` گیت می‌کنه (کد نامعتبر/رویداد نادرست/لغوشده/قبلاً چک‌این‌شده) و `Registration.status` رو `CHECKED_IN` می‌کنه + `checked_in_at`/`checked_in_by_user_id`. QR بلیط سمت فرانت (`TicketQrCode.tsx`) لینک کامل `/organizer/events/{id}/checkin?code=...` رو کد می‌کنه (نه متن خام کد بلیط) تا با دوربین عادی گوشی هم باز بشه، نه فقط اسکنر داخل اپ (`html5-qrcode`، صفحه‌ی `organizer/events/[id]/checkin`).
- **حذف کامل رویداد (ادمین):** برخلاف تصمیم اولیه‌ی فاز ۵ (حذف واقعی و برگشت‌ناپذیر)، از فاز ۶ به بعد **soft delete** است — تصمیم صریح کاربر تا هم دیتا برای بازیابی/بررسی بمونه هم `admin_audit_log` بی‌معنی نشه. `admin_service.soft_delete_event` فقط `event.deleted_at = utcnow()` می‌زنه (+ حذف از ایندکس جستجو)، هیچ ردیفی واقعاً پاک نمی‌شه. `event_service.event_query()` (نقطه‌ی مشترک همه‌ی لیستینگ/جزئیات عمومی) و `admin_service.list_all_events` هر دو `Event.deleted_at.is_(None)` رو فیلتر می‌کنن، پس رویداد soft-delete شده خودکار از همه‌جای عمومی و از لیست خود پنل ادمین هم ناپدید می‌شه، بدون این‌که واقعاً از DB بره. هر FK جدیدی که به `events.id` اضافه می‌کنی (مثل `NotificationOutbox.event_id`) نیازی به دستکاری این منطق نداره چون دیگه هیچ حذف واقعی‌ای در کار نیست.
- **صف اعلان‌ها (فاز ۶):** `NotificationOutbox` (channel=sms/email، template_key، payload_json، status، next_attempt_at) صف مشترک هر ۳ قالب (`REGISTRATION_COMPLETE`/`TICKET_PURCHASE_COMPLETE`/`EVENT_REMINDER_1H`) است. کد سرویس هرگز مستقیم provider رو صدا نمی‌زنه؛ فقط `notification_service.enqueue(...)` یه سطر می‌سازه. ارسال واقعی فقط تو `app/workers/scheduler.py` (پردازه‌ی جدا، `python -m app.workers.scheduler`، دو job: دیسپچر صف هر ۱۵ ثانیه + اسکنر یادآوری ۱ساعته هر ۶۰ ثانیه) اتفاق می‌افته. `complete_order` (سفارش رایگان یا پولی، فرقی نداره) قلاب `notify_registration_complete` رو صدا می‌زنه — چون این پروژه «ثبت‌نام» جدا از «خرید» نداره. برخلاف ایندکس جستجو (دام #۲۱)، این enqueue فقط یه INSERT محلیه نه I/O شبکه‌ای، پس try/except ساده (بدون thread/timeout) کافیه.
- **تاریخ/ساعت جلالی سمت سرور:** برای متن پیامک/ایمیل (که مرورگری در کار نیست تا خودش timezone/calendar رو حدس بزنه، برخلاف `lib/date.ts` فرانت که از `Intl` مرورگر استفاده می‌کنه) از `app/core/persian_date.py: format_jalali_datetime(dt)` استفاده کن، نه یه تبدیل دستی جدید. وابسته به `jdatetime` + `tzdata` (این یکی روی ویندوز/Docker slim اجباریه، `zoneinfo` بدونش fail می‌ده).
- **نظر رویداد (۴محوره) در برابر امتیاز ساده (فاز ۷):** این دو مسیر قرینه‌ی هم نیستن. `POST /events/{id}/reviews` گیت سخت داره — `review_service._find_eligible_registration` فقط به کسی اجازه می‌ده که `Registration.status=CONFIRMED` واقعی داشته باشه **و** `EventSession.starts_at` جلسه‌ش گذشته باشه (قبل از برگزاری نمی‌شه نظر داد)؛ submit دوباره = ویرایش نظر قبلی (create-or-update، نه رد duplicate)، و `event.rating_avg`/`rating_count` بعد از هر submit/hide/unhide از میانگین نظرهای `PUBLISHED` بازمحاسبه می‌شه. در مقابل `POST /ratings {entity_type: instructor|organizer|platform, score}` هیچ گیتی نداره (هر کاربر لاگین‌کرده می‌تونه امتیاز بده) و میانگینش **همیشه زنده محاسبه می‌شه، نه denorm** — هم‌راستا با الگوی `follower_count` زنده‌ی همین پروژه، نه رول‌آپ شبانه. `GET /events?sort=top_rated` و بخش «برترین وبینارها»ی صفحه‌ی اصلی هر دو از یک کف مشترک `home_service.MIN_RATING_COUNT_FOR_TOP_RATED=3` استفاده می‌کنن (در `events.py` ایمپورت می‌شه، تکرار نکن). جزئیات کامل در `specs/spec7.md`.

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

# ورکر اعلان‌ها (فاز ۶) — پردازه‌ی کاملاً جدا، اختیاری برای توسعه‌ی محلی
# (بدون این، سفارش‌ها/ثبت‌نام‌ها هنوز کامل می‌شن، فقط چیزی از notification_outbox خارج نمی‌شه)
python -m app.workers.scheduler

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
11. **شادکن `Select` بر پایه‌ی Base UI (نه Radix) پیش‌فرض value خام رو نشون می‌ده، نه لیبل آیتم متناظرش.** برخلاف Radix که `SelectValue` خودکار لیبل انتخاب‌شده رو رندر می‌کنه، اینجا باید صریحاً یه children (تابع) به `SelectValue` بدی که value رو به لیبل نگاشت کنه (`<SelectValue>{(v) => LABELS[v] ?? v}</SelectValue>`) — وگرنه کاربر مثلاً «۹» یا «online» می‌بینه به‌جای «ادبیات»/«آنلاین». همین قاعده برای `Combobox` هم صادقه (`components/ui/combobox.tsx`، بر پایه‌ی `@base-ui/react/combobox`) — آیتم‌ها رو به شکل `{value, label}` بده تا خودکار درست کار کنه.
12. **هر endpoint‌ای که با کوکی refresh چرخشی (rotating) کار می‌کنه رو هرگز از دو جای مختلف هم‌زمان صدا نزن.** چون هر فراخوانی توکن قبلی رو باطل و یکی جدید صادر می‌کنه، دو فراخوانی هم‌زمان با همون کوکی اولیه (مثلاً به‌خاطر React StrictMode که effectها رو دوبار در dev اجرا می‌کنه) باعث می‌شه فراخوانی دوم به‌عنوان «استفاده‌ی مجدد از توکن باطل‌شده» (سرقت) تشخیص داده بشه و کل session باطل بشه. اگه یه effect سراسری قراره `/auth/refresh` رو موقع لود صفحه صدا بزنه (مثل `SessionBootstrap.tsx`)، حتماً با یه promise سطح‌ماژول (نه state) تضمین کن فراخوانی حداکثر یک‌بار در طول عمر صفحه اتفاق بیفته.
13. **input نیتیو مرورگر `type="datetime-local"` همیشه با تقویم میلادی نمایش داده می‌شه، مهم نیست چی تو `lang`/`dir` صفحه باشه** — این محدودیت خود مرورگره (Chrome/Firefox/Safari هیچ‌کدوم پشتیبانی تقویم جلالی برای این input ندارن)، نه چیزی که با CSS/locale حل بشه. برای فیلد تاریخ/ساعت شمسی تعاملی، از `components/JalaliDateTimePicker.tsx` (بر پایه‌ی `react-multi-date-picker` + `react-date-object`) استفاده کن — مقدار ورودی/خروجیش همیشه رشته‌ی ISO میلادیه، فقط نمایش شمسیه. (این با `lib/date.ts` فرق داره: اونجا فقط *نمایش* یک‌طرفه‌ی تاریخ با `Intl` بومیه، نه یه picker تعاملی — `Intl` برای ساخت calendar grid تعاملی کافی نیست.)
14. **`react-multi-date-picker`/`react-date-object` با locale فارسی (`persian_fa`) پیش‌فرض فرم خلاصه‌ی اسم روزهای هفته رو نشون می‌ده** (مثلاً «شن» به‌جای «شنبه» — چون locale خودش هر روز رو به‌صورت تاپل `[نام‌کامل, خلاصه]` تعریف کرده و کتابخونه پیش‌فرض عضو دوم رو رندر می‌کنه). برای نام کامل، prop جدای `weekDays` رو صریح override کن (نمونه در `JalaliDateTimePicker.tsx`). همچنین چون ردیف هدر روزها عرضش رو از ردیف اعداد (که خودش تنگه) به ارث می‌بره، برای جا باز کردن اسم کامل باید `min-width` کل تقویم رو هم تو CSS بزرگ‌تر کرد (نگاه کن به `globals.css`، بخش `.rmdp-*`).
15. **دو تا guard جدا برای «رفرش خودکار access token» (یکی موقع لود صفحه، یکی موقع برخورد به ۴۰۱) اصلاً کافی نیست** — باید هردو از **همون یک** promise سطح‌ماژول تک‌پرواز استفاده کنن (`lib/api-client.ts: refreshAccessToken()`)، وگرنه دو مسیر جدا می‌تونن هم‌زمان `/auth/refresh` رو با همون کوکی چرخشی صدا بزنن و دقیقاً همون مشکل تشخیص سرقت (دام #۱۲) رخ بده. `request()` و `uploadFileWithProgress()` هردو روی ۴۰۱ (فقط وقتی `accessToken` واقعاً پاس داده شده بود) یک‌بار `refreshAccessToken()` رو صدا می‌زنن و درخواست اصلی رو با توکن تازه تکرار می‌کنن — چون access token فقط ۱۵ دقیقه اعتباره، بدون این مکانیزم هر فرم طولانی (مثل ایجاد رویداد با جلسه‌های زیاد) بعد از ۱۵ دقیقه با «توکن نامعتبر یا منقضی‌شده» fail می‌کرد.
16. **در Docker build بک‌اند، `apt-get update`/`install` می‌تونه رو شبکه‌ی این محیط به‌طور کامل گیر کنه یا timeout بده** (بدون خطای واضح، فقط خیلی کند/بی‌نتیجه) — قبل از افزودن `build-essential` یا هر پکیج apt دیگه، اول چک کن آیا واقعاً لازمه: اکثر پکیج‌های pip (از جمله `cryptography`, `Pillow`, `pymongo`) برای `python:3.12-slim` روی `linux/amd64` از قبل wheel آماده دارن و کامپایلر نمی‌خوان. همچنین `pip install` گاهی با خطای `THESE PACKAGES DO NOT MATCH THE HASHES` روی دانلود پکیج‌های خیلی بزرگ (مثل wheelهای CUDA/nvidia که transitive dependency ی سنگین کتابخونه‌هایی مثل `sentence-transformers`ان) fail می‌کنه — این معمولاً یعنی دانلود ناقص/خراب روی شبکه‌ی ناپایدار این محیط بوده، نه واقعاً تهدید امنیتی؛ راه‌حل بهتر از retry صرف، حذف اون وابستگی سنگین از `requirements.txt` تا زمانی که واقعاً لازم بشه (نمونه: `chromadb`/`sentence-transformers` که فاز ۴ هنوز شروع نشده کامنت شدن).
17. **اجرای `npm run build` برای تأیید نهایی، درحالی‌که `npm run dev` هم‌زمان روی همون پوشه‌ی `frontend/` در حال اجراست، `.next/` مشترک رو خراب می‌کنه** (build خروجی production می‌نویسه، dev سرور با webpack/HMR خودش گیج می‌شه — نشونه‌ی معمول: چانک‌های `/_next/static/...` با ۴۰۴ خام fail می‌شن، نه صفحه‌ی خطای Next.js). بعد از هر `npm run build` تأییدی، اگه `npm run dev` قراره ادامه بده، حتماً dev server رو kill کن، `rm -rf .next`، و دوباره `npm run dev` بزن — وگرنه تست بصری بعدی (خود کاربر یا خودت با curl) نتیجه‌ی خراب/قدیمی می‌بینه و به‌اشتباه فکر می‌کنی feature یا فیکس تازه باگ داره.
18. **اضافه‌کردن یک router جدید (فایل تازه) به بک‌اند، یا هر import جدید در `main.py`، با uvicorn بدون `--reload` اصلاً پیک‌آپ نمی‌شه** — نه فقط تغییر کد endpoint موجود (که در نکته‌ی #۲ گفته شده)، بلکه خود endpointهای جدید تا restart دستی اصلاً تو `/openapi.json` ظاهر نمی‌شن؛ راحت‌ترین تشخیص: بعد از افزودن route جدید، `curl .../openapi.json` بزن و چک کن مسیر جدید توش هست یا نه، قبل از این‌که فکر کنی کد اشتباهه.
19. **`react-hooks/set-state-in-effect` هر تابع محلی (تو همون کامپوننت تعریف‌شده) که مستقیم/غیرمستقیم setState صدا می‌زنه رو، اگه از دل یک effect صداش بزنی، فلگ می‌کنه — حتی اگه اون تابع `async` باشه و setState فقط بعد از `await` بیاد** (مثلاً `await Promise.resolve()` اول تابع، کاری نمی‌کنه؛ لینتر static-analysis می‌کنه نه runtime). این با `useEffect(() => { refreshAccessToken(); }, [])` تو `SessionBootstrap.tsx` فرق داره چون اونجا `refreshAccessToken` از یه ماژول **دیگه** import شده (`api-client.ts`)، نه تو خود کامپوننت تعریف نشده. راه‌حل واقعی، نه دور زدن قانون: کار رو از دل یک event handler واقعی صدا بزن (کلیک دکمه، بعد از تأیید OTP)، نه effect. برای «شروع خودکار وقتی از قبل یه پیش‌شرط برقراره» (مثلاً کاربر لاگین‌کرده)، به‌جای effect + reset، از یه initial state متفاوت (lazy `useState(() => ...)`) و یه قدم تأیید دستی کاربر استفاده کن — نمونه در `InstantRegisterModal.tsx` (مرحله‌ی «تأیید» قبل از ثبت‌نام خودکار). نکته‌ی مرتبط: اگه اون تابع فقط `setLoading(true)` می‌زنه و state پیش‌فرض `loading` از قبل `true`ه، ساده‌ترین فیکس حذف همون یک خط `setLoading(true)`ه، نه بازطراحی کل effect — نمونه در `app/admin/page.tsx: loadAll()`.
20. **اضافه‌کردن یک مدل SQLAlchemy جدید (فایل تازه در `app/models/`) کافی نیست تا Alembic autogenerate ببینتش** — باید صریح به `app/models/__init__.py` (هم import هم `__all__`) اضافه بشه، وگرنه `alembic revision --autogenerate` بی‌صدا یه migration خالی (`pass`/`pass`) تولید می‌کنه، بدون هیچ خطا یا هشداری. علامت تشخیص: بعد از autogenerate، اگه پیام `Detected added table/column` تو خروجی نبود، migration خالیه — قبل از commit کردنش پاکش کن، مدل رو به `__init__.py` اضافه کن، و autogenerate رو دوباره بزن.
21. **«try/except دور یه فراخوانی» کافی نیست تا یه side-effect جانبی (مثل ایندکس جستجو) کاربر رو معطل نکنه** — اگه اون فراخوانی هیچ‌وقت واقعاً exception نده (نه fail کنه نه موفق بشه)، فقط خیلی کند باشه، try/except هیچ کمکی نمی‌کنه چون اصلاً چیزی گیر نمی‌ندازه. دقیقاً این اتفاق افتاد: دانلود اولیه‌ی مدل embedding (فاز ۴) روی شبکه‌ی این محیط داده رو خیلی کند trickle می‌کرد بدون قطعی کامل، پس نه `HF_HUB_DOWNLOAD_TIMEOUT` کمک کرد نه try/except، و `PATCH /events/{id}` چند دقیقه معطل می‌موند. راه‌حل واقعی: خود عملیات رو تو یه `ThreadPoolExecutor` جدا اجرا کن و رو `future.result(timeout=N)` صبر کن — اگه ظرف N ثانیه تموم نشد، درخواست اصلی بدون اثر منفی ادامه بده (نمونه‌ی کامل: `event_service._safe_sync_event_index`). این الگو رو برای هر «بهبود جانبی که نباید بخش اصلی تراکنش رو بلاک کنه» به کار ببر، نه فقط جستجو.

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
- OTP-only به‌عنوان روش اصلی لاگین می‌مونه (نه Google Sign-In — ریسک دسترسی/تحریم برای پلتفرم ایرانی)؛ ولی تکمیل نام و نام خانوادگی قبل از ایجاد رویداد یا خرید بلیط **اجباری**ه (`core/permissions.py: require_complete_profile`) — پیاده شد
- Refresh token: ۱ روز (نه ۳۰ روز طرح اولیه‌ی architecture.md) — کاربر بعد از بحث گفت ۳۰ روز زیاده، مقایسه کرد با رفتار معمول JWT در سایت‌های دیگه («بعد یک روز لاگ‌اوت می‌شی»)؛ `settings.refresh_token_expire_days` در `config.py`/`.env.example`

## مرجع‌های بیرونی مهم

- `docs/event_otp_email_sms_plan_fa.md` — سند اصلی مکانیزم OTP (کاربر نوشته، منبع حقیقت برای پارامترهای OTP)
- `data/eseminar.tv/analysis.md`, `data/evand.com/analysis.md` — تحلیل رقبا، پایه‌ی بسیاری از تصمیمات UX
- `specs/README.md` — قرارداد نگهداری فایل‌های spec، بخون قبل از نوشتن spec فاز جدید
