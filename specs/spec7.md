# فاز ۷ — امتیاز/نظر ۴محوره + امتیاز ساده مدرس/برگزارکننده/سایت

وضعیت: ✅ کامل (بک‌اند + فرانت)، تست‌شده، لینت/تایپ تمیز، زنده روی سرور dev تأیید شد.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن + سیستم مدرس/آواتار/تکمیل پروفایل اجباری. فاز ۴: جستجوی معنایی (ChromaDB) + صفحه‌ی اصلی Redis-cached + ثبت‌نام فوری. فاز ۵: پنل ادمین (رویدادها/کاربران/دسته‌بندی/لاگ اقدامات). فاز ۶: صف اعلان‌ها (SMS/Email) + worker زمان‌بند + یادآوری ۱ساعته + soft-delete رویداد. جمعاً ۲۵۵ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec6.md`](spec6.md).

## هدف

بخش ۳ پلن معماری، تصمیم کاربر #۲: نظر ۴محوره‌ی رویداد باید خودش منبع مستقیم `events.rating_avg` باشه (نه یک مکانیزم امتیازدهی جدا)، و امتیاز مدرس/برگزارکننده/سایت یک ضربه‌ی ساده‌ی ۱-۵ ستاره بدون محور بمونه. هدف نهایی: بخش «برترین وبینارها»ی صفحه‌ی اصلی (که در فاز ۴ چون امتیازدهی وجود نداشت عمداً حذف شده بود) از داده‌ی واقعی پر بشه.

## چیزی که ساخته شد

### بک‌اند

- **مدل `EventReview`** (`app/models/review.py`): چهار محور مستقل هرکدام ۰ تا ۵ — `axis_content_uptodate` (محتوا/به‌روز بودن)، `axis_instructor_mastery` (تسلط مدرس)، `axis_value_for_price` (ارزش به قیمت)، `axis_experience_driven` (تجربه‌ی برگزاری) — به‌علاوه‌ی `overall_computed` (میانگین محاسبه‌شده، denorm)، `comment_text`، `status` (`PUBLISHED`/`HIDDEN`)، `hidden_reason`، `registration_id` (FK — گیت واقعی بودن نظر)، `unique(user_id, event_id)`.
- **مدل‌های `InstructorRating`/`OrganizerRating`/`PlatformRating`** (`app/models/rating.py`): برخلاف `EventReview`، بدون محور — فقط `score:int` ۱ تا ۵، `unique(user_id, entity)`. سه جدول جدا به‌جای یک جدول پلی‌مورفیک، طبق تصمیم قبلی معماری (#۸، یکپارچگی FK واقعی در SQLite).
- **Migration**: `80fd837094a4_reviews_and_ratings.py`.
- **`app/services/review_service.py`**:
  - `_find_eligible_registration`: گیت سخت — کاربر باید یک `Registration` با `status=CONFIRMED` روی همون رویداد داشته باشه **و** `EventSession.starts_at` جلسه‌ش گذشته باشه (نمی‌شه قبل از برگزاری نظر داد). این قاعده‌ی کسب‌وکار در `architecture.md` صراحتاً نیومده، ولی به‌عنوان یک الزام بدیهی («اول شرکت کن، بعد نظر بده») در همین فاز تصمیم‌گیری و پیاده شد.
  - `submit_review`: **create-or-update**، نه رد duplicate — ارسال دوباره‌ی نظر همون کاربر روی همون رویداد جایگزین نظر قبلی می‌شه (unique constraint روی `user_id+event_id`).
  - `_recompute_event_rating`: بعد از هر submit/hide/unhide، `event.rating_avg`/`rating_count` از میانگین فقط نظرهای `PUBLISHED` بازمحاسبه می‌شه.
  - `list_event_reviews`: فقط `PUBLISHED` برمی‌گردونه (عمومی).
  - `set_review_hidden`: برای ادمین — تغییر status + بازمحاسبه‌ی امتیاز رویداد.
- **`app/services/rating_service.py`**: `rate_instructor/rate_organizer/rate_platform` (upsert روی امتیاز ۱-۵)، `instructor_rating_stats/organizer_rating_stats/platform_rating_stats` (میانگین+تعداد **همیشه زنده محاسبه می‌شه، نه denorm** — دقیقاً هم‌راستا با الگوی `follower_count` زنده‌ی همین کدبیس، نه رول‌آپ شبانه‌ی `popularity_score` که در `architecture.md` برای مقیاس بزرگ‌تر پیش‌بینی شده)، `my_instructor_rating/my_organizer_rating`.
- **Endpointها**:
  - `POST /events/{id}/reviews` (auth اجباری، rate-limit `5/minute`)، `GET /events/{id}/reviews` (عمومی، فقط PUBLISHED) — در `events.py`.
  - `POST /ratings {entity_type, entity_id?, score}` (auth اجباری، rate-limit `20/minute`، dispatch روی `entity_type` ∈ {instructor, organizer, platform}) — router جدید `app/api/v1/routers/ratings.py`، در `main.py` رجیستر شد.
  - `GET /instructors/{id}` و `GET /organizers/{id}` حالا `rating_avg`/`rating_count`/`my_rating` رو هم برمی‌گردونن.
  - ادمین: `GET /admin/reviews` (شامل hidden، برای مدیریت) + `PATCH /admin/reviews/{id}/hide` (بدنه‌ی `HideReviewIn{hidden, reason}`) — مثل هر endpoint نوشتنی دیگه‌ی ادمین، `admin_service.log_action("hide_review"/"unhide_review", ...)` رو صدا می‌زنه.
- **`home_service.py`**: ثابت `MIN_RATING_COUNT_FOR_TOP_RATED = 3` (بخش ۱۰ پلن: کف نظر برای جلوگیری از این‌که یک نظر ۵ستاره‌ی تنها رتبه‌ی اول رو بگیره) + تابع `_top_rated_events()`، وایر شده به `GET /home/sections`. همین ثابت در `events.py` هم برای شاخه‌ی جدید `sort=top_rated` روی `GET /events` ایمپورت و استفاده شد (تا عدد جادویی در دو جا تکرار نشه).

### فرانت‌اند

- **`StarRating.tsx`**: کامپوننت مشترک نمایش/دریافت امتیاز، `value`/`onRate?`/`readOnly?`/`size?`، همیشه `dir="ltr"` داخلی (قرارداد جهانی مقیاس ستاره‌ای، مستقل از RTL بقیه‌ی سایت).
- **`EventReviews.tsx`**: روی صفحه‌ی جزئیات رویداد — فرم ثبت نظر ۴محوره (فقط وقتی `accessToken` بعد از هیدریت موجوده نمایش داده می‌شه) + لیست نظرهای موجود؛ خطای گیت بک‌اند (مثلاً «هنوز واجد شرایط نظر دادن نیستید») عیناً به کاربر نشون داده می‌شه، نه یک پیام عمومی.
- **`RateEntityWidget.tsx`**: ویجت امتیازدهی ستاره‌ای مشترک برای `entityType: "instructor"|"organizer"` — دقیقاً همون الگوی `FollowInstructorButton`/`ClaimInstructorButton`: سرور بدون `accessToken` رندر می‌شه، `my_rating` واقعی بعد از هیدریت با یک فراخوانی کلاینت جدا گرفته می‌شه.
- صفحه‌ی اصلی: کاروسل «برترین وبینارها» (`top_rated_events`) به‌عنوان **اولین** کاروسل، قبل از «وبینارهای محبوب»، لینک «مشاهده همه» به `/events?sort=top_rated`.
- `events/page.tsx`: منطق heading برای `sort === "top_rated"` → «برترین وبینارها».
- `instructors/[id]/page.tsx` / `organizers/[id]/page.tsx`: `RateEntityWidget` وایر شد؛ صفحه‌ی برگزارکننده اولین `Breadcrumbs`ش رو هم همین‌جا گرفت (قبلاً در رول‌اوت breadcrumb فاز قبل جا افتاده بود).
- **کشف جانبی حین کار**: `organizers-api.ts` تا این لحظه هیچ تابع کلاینتی نداشت (فقط یک type) — صفحه‌ی عمومی برگزارکننده فقط از `socialApi.myFollows()` برای وضعیت دنبال‌کردن استفاده می‌کرد، هیچ‌وقت جزئیات کامل برگزارکننده رو سمت کلاینت نمی‌گرفت. برای `RateEntityWidget` یک `organizersApi.getById(id, accessToken)` واقعی اضافه شد — یک شکاف معماری واقعی که همین فاز برطرف شد.

## نکات/دام‌های این فاز

- **گیت نظر ≠ گیت امتیاز ساده**: نظر ۴محوره‌ی رویداد نیاز به ثبت‌نام تأییدشده + گذشتن زمان جلسه داره، ولی امتیاز ساده‌ی مدرس/برگزارکننده/سایت هیچ گیتی نداره (هر کاربر لاگین‌کرده می‌تونه امتیاز بده) — این دو مسیر عمداً قرینه‌ی هم نیستن، چون معنای کسب‌وکارشون فرق می‌کنه (نظر رویداد = گواهی حضور واقعی؛ امتیاز مدرس/برگزارکننده = برداشت کلی، نیازی به یک رویداد خاص نداره).
- **میانگین زنده، نه denorm، برای رتبه‌بندی‌های ساده**: وسوسه‌ی اول اضافه‌کردن `rating_avg` denorm به جدول `Instructor`/`Organizer` هم مثل رویداد بود، ولی چون این پروژه از قبل الگوی `follower_count` زنده رو برای همین دو موجودیت جا انداخته (فاز ۳)، برای یکدستی همون الگو (`COUNT`/`AVG` زنده در هر request) برای امتیاز هم انتخاب شد — نه یک تصمیم عملکردی، یک تصمیم قوام معماری.
- **مقدار `MIN_RATING_COUNT_FOR_TOP_RATED` باید بین `home_service` و `events.py` مشترک بمونه**: چون دو مسیر جدا (بخش صفحه‌ی اصلی + `GET /events?sort=top_rated`) از همون آستانه استفاده می‌کنن، مقدار در `home_service.py` تعریف و در `events.py` ایمپورت شد تا یک تغییر آینده (مثلاً کف ۳ به ۵) در دو جا فراموش نشه.

## راستی‌آزمایی

- `ruff check .` تمیز، `pytest -q` → **۲۸۷ تست پاس** (۲۵۵ قبلی + ۳۲ تست جدید بین دو commit: گیت عدم-ثبت‌نام/قبل-از-شروع نظر، create-or-update، hide/unhide و بازمحاسبه‌ی امتیاز رویداد، آستانه‌ی `top_rated` در home و در `GET /events`، رد امتیاز خارج از بازه‌ی ۱-۵، ratings API برای هر سه `entity_type`).
- فرانت: `npm run build` و `npx eslint src --max-warnings=0` تمیز، `tsc --noEmit` تمیز.
- زنده روی سرور dev: بعد از restart دستی uvicorn، مسیرهای جدید (`/events/{id}/reviews`, `/ratings`, `/admin/reviews`) در `openapi.json` تأیید شدن.

## Commitهای مرتبط

- `f076b20` — `feat(backend): فاز ۷ - امتیاز/نظر ۴محوره رویداد + امتیاز ساده مدرس/برگزارکننده/سایت`
- `f5e9d0a` — `feat(frontend): فاز ۷ - فرم نظر ۴محوره + امتیازدهی ستاره‌ای مدرس/برگزارکننده + بخش «برترین وبینارها»`
