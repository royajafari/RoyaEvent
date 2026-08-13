# فاز ۳ — بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن

وضعیت: ✅ کامل (بک‌اند + فرانت‌اند)، تست‌شده، لینت/build تمیز، تأیید بصری end-to-end واقعی انجام‌شده.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل (دسته‌بندی دوسطحی، جلسه، آپلود بنر امن، صفحه‌ی عمومی SSR). جمعاً ۱۰۱ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)، [`spec1.md`](spec1.md)، [`spec2.md`](spec2.md).

## هدف

خریدار بتونه بلیط رایگان/پولی (شبیه‌سازی‌شده) با کد تخفیف بخره، به رویداد/برگزارکننده علاقه‌مند/دنبال‌کننده بشه، و برگزارکننده بتونه شرکت‌کنندگان رو مدیریت/export کنه.

## چیزی که ساخته شد

### بک‌اند

- مدل‌ها: `TicketType` (با `is_early_bird`)، `DiscountCode` (سطح رویداد)، `PlatformDiscountCode` (سطح سایت/ادمین)، `Order`/`OrderItem`/`Payment`/`Registration`، `Favorite`، `OrganizerFollow`/`InstructorFollow` — `app/models/ticket.py`, `order.py`, `favorite.py`.
- Migration `956ea659d2be` روی پایه‌ی `567deeea1757` (فقط create، بدون drop).
- `app/services/ticket_service.py` — `is_early_bird_active(event)`: فعاله اگر کمتر از یک‌سوم بازه‌ی «شروع فروش تا اولین جلسه» گذشته باشه؛ مرجع «شروع رویداد» = زودترین جلسه (ساده‌سازی برای رویداد چندجلسه‌ای).
- `app/services/discount_service.py` — `find_valid_discount()` اول سطح رویداد بعد سطح سایت رو چک می‌کنه؛ `compute_discount_amount()` percent/fixed.
- `app/services/order_service.py` — `create_order()` (اعتبارسنجی ticket/session/ظرفیت/early-bird/تخفیف، PENDING می‌سازه)، `complete_order()` (finalize، Registration با ticket_code یکتا می‌سازه، quantity_sold +۱، discount uses_count +۱ — پرداخت همیشه شبیه‌سازی می‌شه، بدون درگاه واقعی)، `cancel_registration()` (ظرفیت رو برمی‌گردونه).
- `app/services/social_service.py` — toggle ساده برای favorite/organizer-follow/instructor-follow + `list_my_follows()`.
- `app/core/calendar.py` — `google_calendar_link()`: تابع محض تولید URL، بدون OAuth (طبق تصمیم کاربر).
- `app/core/permissions.py` — `require_event_owner()` منتقل شد این‌جا (قبلاً تکراری در events.py بود)؛ `event_service.py` هم `event_query()`/`to_list_item_out()` عمومی شدن تا `social.py` هم ازشون استفاده کنه.
- Routerها: `tickets.py` (ticket-types CRUD + discount-codes رویداد/ادمین + validate)، `orders.py` (create/complete/get/me-tickets/cancel/calendar-link)، `social.py` (favorites + follows + `GET /me/follows`)، `organizer.py` (attendees list/remove/export CSV). مجموعاً ۳۶ route در `main.py`.
- `Event.organizer` relationship + `organizer_name` property (`full_name or phone or email` — چون کاربرهای OTP-only معمولاً `full_name` ندارن)؛ `EventDetailOut.organizer_name`؛ `event_query()` حالا `selectinload(Event.organizer)` هم داره.

**کد رویداد (event_code) — فرمت به‌روزشده:** از `RE-XXXXXX` (پیشوند ثابت `RE` برای RoyaEvent + ۶ رقم تصادفی امن، مثل `RE-482913`) تولید می‌شه — `app/core/slug.py: generate_event_code()`. این تغییر به درخواست صریح کاربر اضافه شد («یه کلمه کلیدی برای RoyaEvent اضافه کن») تا کد رویداد قابل‌تشخیص از رقبا باشه (در فاز ۲ فقط عددی خالص بود). برای URL/slug، نسخه‌ی lowercase کد به انتهای slug اضافه می‌شه، ولی خودِ `event_code` ذخیره‌شده و نمایشی uppercase می‌مونه.

**تست‌ها:** `test_ticket_service.py` (۸)، `test_discount_service.py` (۱۱)، `test_order_service.py` (۱۷)، `test_social_service.py` (۵) در unit/؛ `test_tickets_api.py` (۹)، `test_orders_api.py` (۱۲)، `test_social_api.py` (۷)، `test_organizer_api.py` (۵) در integration/. فیکسچرهای جدید در `conftest.py`: `buyer`/`buyer_auth_headers`، `admin_user`/`admin_auth_headers`، `published_event`، `free_ticket_type`/`paid_ticket_type`. **مجموع تست تا این فاز: ۱۷۳.**

### فرانت‌اند

- `lib/tickets-api.ts` — `TicketType`, `ticketsApi.listByEvent`, `ticketsApi.validateDiscount`.
- `lib/orders-api.ts` — `Order`, `Registration`, `MyTicket`, `ordersApi.create/complete/get/myTickets/cancelRegistration/calendarLink`.
- `lib/social-api.ts` — `socialApi.addFavorite/removeFavorite/myFavorites/followOrganizer/unfollowOrganizer/followInstructor/unfollowInstructor/myFollows`.
- `lib/organizer-api.ts` — `organizerApi.listAttendees/removeAttendee/downloadAttendeesCsv`.
- `components/TicketCheckout.tsx` — انتخاب نوع بلیط (کارت‌های کلیک‌پذیر، نه Select)، انتخاب جلسه (اگه چندجلسه‌ای)، فیلد کد تخفیف، ثبت‌نام یک‌مرحله‌ای (create+complete پشت‌سرهم چون پرداخت شبیه‌سازی‌شده‌ست).
- `components/StickyTicketFooter.tsx` — نوار پایین صفحه با قیمت ارزان‌ترین بلیط + دکمه‌ی اسکرول به `#ticket-checkout`.
- `components/FavoriteButton.tsx`, `components/FollowOrganizerButton.tsx` — فقط وقتی `accessToken` هست رندر می‌شن؛ وضعیت اولیه از `GET /me/favorites` / `GET /me/follows`.
- `app/tickets/page.tsx` — «بلیط‌های من»: لیست، لغو ثبت‌نام، افزودن به تقویم.
- `app/(organizer)/organizer/events/[id]/attendees/page.tsx` — داشبورد شرکت‌کنندگان برگزارکننده + export CSV. مسیرش `/organizer/events/[id]/attendees` است (نه `/events/[id]/attendees`) — دلیل در بخش دام‌ها.
- `app/events/[slug]/page.tsx` به‌روز شد: بخش برگزارکننده (نام + `FollowOrganizerButton`)، `FavoriteButton` کنار عنوان، `<TicketCheckout>` (فقط `published`)، `<StickyTicketFooter>` (فقط `published`)، `pb-24` برای جا باز کردن زیر فوتر چسبان.
- لینک «بلیط‌های من» به `SiteHeader` اضافه شد.
- **تصمیم عمدی (اسکوپ محدود این پاس):** دکمه‌ی favorite روی کارت‌های لیستینگ (`EventCard`) اضافه نشد — چون صفحات لیستینگ Server Component هستن و بدون context کاربر؛ اضافه‌کردن N بررسی وضعیت به‌ازای هر کارت یعنی fetch storm. فعلاً فقط در صفحه‌ی جزئیات رویداد.

### پرداخت بصری بعد از تکمیل فاز (polish کوچک، همون commit-run)

- کاربر تصویر لوگو رو دید و گفت پس‌زمینه‌ی هدر باید همون navy تیره‌ی لوگو باشه تا حرف سفید لوگو گم نشه، و بعد خواست کل پس‌زمینه‌ی سایت با پس‌زمینه‌ی لوگو یکی بشه (کاربر متوجه مرز نشه). راه‌حل نهایی: کلاس `dark` به‌صورت دائمی روی `<html>` در `app/layout.tsx` اضافه شد (نه یک toggle) — چون `globals.css` از فاز ۲ کامل رنگ‌های dark mode (`--background: var(--brand-dark)` و بقیه‌ی توکن‌ها) رو داشت، فقط فعال نبود. با فعال‌شدنش کل سایت (هدر + بدنه + کارت‌ها) یکدست navy شد، بدون نیاز به جعبه‌ی جدا پشت لوگو.

### بعد از فاز — پیاده‌سازی «آپلود کلیپ کوتاه تبلیغاتی» از لیست کارهای درخواستی

این آیتم اول لیست «کارهای درخواستی در صف» بود (CLAUDE.md)؛ کنار بنر، نه جایگزینش.

- بک‌اند: `Event.promo_video_url` (String(500), nullable) — migration `5c8b87af0219` روی پایه‌ی `956ea659d2be` (فقط add column). `app/services/video_service.py: validate_video_file()` فرمت رو از روی magic bytes تشخیص می‌ده (MP4: بایت ۴-۷ باید `ftyp` باشه؛ WebM: ۴ بایت اول باید `1A 45 DF A3` باشه — EBML header)، سقف حجم ۳۰ مگابایت، **بدون transcode واقعی** (تصمیم آگاهانه‌ی MVP، برخلاف بنر که کامل re-encode می‌شه چون ffmpeg سنگینه). `app/core/storage.py: upload_promo_video()` فایل خام رو با نام تصادفی در `promo-videos/{event_id}/{uuid}.{ext}` ذخیره می‌کنه. Endpoint: `POST /events/{id}/promo-video` (فقط مالک، rate-limit ۱۰/دقیقه، مثل بنر).
- فرانت: `eventsApi.uploadPromoVideo()`. فرم ایجاد رویداد (`create/page.tsx`) یک فیلد آپلود ویدیوی جدا کنار بنر داره. صفحه‌ی جزئیات رویداد: اگه `promo_video_url` باشه، `<video controls preload="metadata">` به‌جای بنر خام نشون داده می‌شه (با `poster={banner_url}` اگه بنر هم باشه)؛ اگه ویدیو نباشه، مثل قبل بنر یا جای‌خالی نشون داده می‌شه.
- **درخواست بعدی کاربر که همین‌جا اضافه شد:** نوار پیشرفت آپلود (درصد لحظه‌ای) برای هر دو فایل (بنر و ویدیو). چون `fetch` امکان دنبال‌کردن upload progress رو نمی‌ده، `lib/api-client.ts: uploadFileWithProgress()` با `XMLHttpRequest` (نه fetch) نوشته شد؛ `xhr.upload.onprogress` درصد رو محاسبه می‌کنه. کامپوننت UI جدید و مینیمال `components/ui/progress.tsx` (بدون کتابخونه‌ی جانبی، فقط دو `div` تو در تو با Tailwind) برای نمایش نوار اضافه شد.
- تست‌ها: `tests/unit/test_video_service.py` (۶ تست: مسیر موفق mp4/webm، رد فایل خالی/غیرویدیو/حجم زیاد/عکس با ادعای پسوند ویدیو) + ۳ تست integration (`test_promo_video_upload_*` در `test_events_api.py`، مشابه الگوی تست‌های بنر، mock روی `upload_promo_video`). مجموع تست بعد از این کار: **۱۸۲**.
- راستی‌آزمایی واقعی: با سرور واقعی (نه mock) یک فایل mp4 مینیمال (فقط magic bytes معتبر) آپلود شد، `promo_video_url` واقعاً در MinIO واقعی ذخیره و از طریق `curl` با `content-type: video/mp4` قابل بازیابی بود؛ HTML خروجی SSR صفحه‌ی رویداد هم تگ `<video preload="metadata">` با همون URL رو نشون داد.

### بعد از فاز — سوییچ object storage به ArvanCloud (سرویس مدیریت‌شده)

کاربر گفته بود دنبال یک سرویس object storage مدیریت‌شده می‌گرده تا خودش MinIO رو نگه‌داری نکنه؛ یک اکانت ArvanCloud Object Storage گرفت (endpoint: `s3.ir-thr-at1.arvanstorage.ir`, bucket: `royaevent`، هم به‌صورت path-style هم virtual-hosted-style عمومی در دسترسه، هردو تست شدن و کار می‌کنن).

- **هیچ تغییر کدی لازم نبود** — `app/core/storage.py` از قبل فقط با `minio-py` (کلاینت عمومی S3-compatible) صحبت می‌کنه، نه با چیزی مخصوص MinIO. فقط `backend/.env` (gitignored) با endpoint/کلید/باکت آروان‌کلود پر شد.
- آروان‌کلود دو جفت کلید در پنلش نشون می‌ده: یک «Access Key/Secret Key» سطح اکانت، و یک کلید جدا برای «کاربر» نام‌گذاری‌شده (`royaevent_admin`). کلید کاربر `royaevent_admin` هنگام `ensure_bucket_ready()` (که `set_bucket_policy` صدا می‌زنه) با `AccessDenied` رد شد — احتمالاً دسترسی مدیریت policy نداره. کلید سطح اکانت (Access Key/Secret Key اول) کار کرد و برای این پروژه استفاده شد.
- **تصمیم صریح کاربر: پیکربندی MinIO محلی حذف نشه**، به‌عنوان سناریوی جایگزین (سناریو ۲) همیشه مستند و در دسترس بمونه. `infra/docker-compose.yml` و کد بدون تغییر موندن؛ فقط `.env.example` (ریشه‌ی ریپو) هر دو سناریو رو کنار هم با کامنت نشون می‌ده — فعال‌سازی هرکدوم فقط تغییر ۵ متغیر `MINIO_*` در `.env` است.
- راستی‌آزمایی: بنر واقعی از طریق endpoint واقعی (`POST /events/1/banner`) آپلود شد، `banner_url` به آدرس واقعی آروان‌کلود اشاره می‌کرد و با `curl` (`content-type: image/jpeg`, ۲۰۰) قابل بازیابی بود؛ کل تست‌سوییت (۱۸۲ تست، mock‌شده) هم بدون تغییر پاس شد چون تست‌ها به storage واقعی وابسته نیستن.
- **نکته‌ی امنیتی:** کلیدهای واقعی مستقیم در چت کاربر پیست شدن (نه در فایل). فقط در `.env` ذخیره شدن، هیچ‌جا (کد/مستندات/کامیت) تکرار نشدن. اگه کاربر نگران لو رفتن این کلیدها از تاریخچه‌ی چته، بهتره از پنل آروان‌کلود rotate/regenerate بشن. (بعداً کاربر واقعاً secret key رو rotate کرد؛ اتصال دوباره با کلید جدید تست و تأیید شد.)

### بعد از فاز — باگ‌های کشف‌شده حین تست بصری زنده‌ی کاربر (بدون Playwright)

چون Playwright در دسترس نیست، کاربر خودش با مرورگر واقعی سایت رو تست کرد و اسکرین‌شات فرستاد؛ چند باگ واقعی همین‌جوری پیدا شد:

1. **باگ session/رفرش صفحه (جدی‌ترین):** بعد از تأیید موفق OTP، `access_token` فقط در حافظه (Zustand) بود و با هر رفرش صفحه پاک می‌شد. هیچ‌جای کد `authApi.refresh()` (که از قبل نوشته شده بود) صدا زده نمی‌شد، پس کاربر بعد از هر F5 انگار لاگ‌اوت می‌شد، حتی با کوکی refresh معتبر. کشفش این‌جوری بود: کاربر گزارش داد OTP قبول نشد؛ چک مستقیم DB نشون داد واقعاً verify شده بود (`status=VERIFIED`) ولی هدر هنوز «ورود» نشون می‌داد — چون **`SiteHeader` اصلاً به `accessToken` واکنش نشون نمی‌داد** (باگ دوم، مستقل). فیکس: `components/SessionBootstrap.tsx` (رندر یک‌بار در `layout.tsx`) با کوکی refresh موقع لود صفحه یه access token تازه می‌گیره. **نکته‌ی حیاتی:** چون refresh token چرخشیه (فاز ۱)، این effect نباید دوبار هم‌زمان صدا بخوره — React StrictMode در dev دقیقاً همین کارو با دوبار اجرای effect می‌کنه و باعث می‌شه فراخوانی دوم به‌عنوان reuse توکن باطل‌شده تشخیص داده بشه و کل session باطل بشه. راه‌حل: یه `bootstrapPromise` سطح‌ماژول (نه state) که تضمین می‌کنه `authApi.refresh()` حداکثر یک‌بار در طول عمر صفحه فراخوانی بشه.
2. **`SiteHeader` واکنش‌گرا نبود:** همیشه «ورود» نشون می‌داد، صرف‌نظر از وضعیت لاگین. فیکس شد به دکمه‌ی «خروج» واقعی (با `authApi.logout()`) وقتی `accessToken` ست باشه.
3. **باگ Select در فرم ایجاد رویداد:** دسته‌بندی «۹» و نوع برگزاری «online» نشون می‌داد (نه لیبل فارسی). علتش: shadcn `Select` بر پایه‌ی Base UI، برخلاف Radix، پیش‌فرض value خام رو تو trigger نشون می‌ده مگه یه children (تابع نگاشت value→لیبل) صریحاً بهش بدی. برای هر ۳ Select (دسته‌بندی، نوع برگزاری، نوع دسترسی) رفع شد.
4. **دسته‌بندی به Combobox قابل‌جستجو تبدیل شد** (درخواست کاربر: «بتونم تایپ کنم تا مشابهش رو زود بیاره») — `components/ui/combobox.tsx` جدید نوشته شد، بر پایه‌ی `@base-ui/react/combobox` (فیلترینگ built-in با `items`/`filter`، گروه‌بندی با `Combobox.Group`+`Combobox.Collection`).
5. **تاریخ‌ساعت جلسه‌ها میلادی بود:** input نیتیو `type="datetime-local"` مرورگر همیشه تقویم میلادی نشون می‌ده، این محدودیت خود مرورگره (نه چیزی که با `lang`/`dir` صفحه حل بشه). `components/JalaliDateTimePicker.tsx` نوشته شد با کتابخونه‌ی `react-multi-date-picker` (+ `react-date-object` برای تقویم/لوکیل فارسی، + پلاگین `time_picker`) — مقدار ورودی/خروجی همیشه ISO میلادیه (سازگار با بک‌اند)، فقط نمایش شمسیه.
6. **داده‌ی تستی خراب:** دو تا ticket type (فاز ۳) که قبلاً با curl مستقیم در Git Bash ساخته شده بودن، اسم‌شون `??????` بود (همون باگ شناخته‌شده‌ی رمزگذاری). چون endpoint PATCH برای ticket-type وجود نداره، مستقیم با یه اسکریپت پایتون در DB اصلاح شد.
7. **کارت خبرنامه‌ی صفحه‌ی اصلی** از اسکلت فاز ۰ کاملاً no-op بود (نه اعتبارسنجی، نه بک‌اند). کاربر اول خواست حذف بشه، بعد نظرش عوض شد و خواست بمونه + حالت «قبلاً عضو شدم». چون بک‌اند خبرنامه هنوز نیست، `components/NewsletterSignup.tsx` با اعتبارسنجی فارسی (`noValidate` روی فرم تا پیام native انگلیسی مرورگر رو خفه کنه) و وضعیت subscribed در `localStorage` نوشته شد.

هیچ‌کدوم این‌ها به فاز ۳ محدود نبودن (بیشترشون باگ‌های زیرساختی/UI-framework بودن که در آینده هم می‌تونستن پیش بیان)؛ نکات کلی‌ترشون (Select label، race condition رفرش‌توکن، محدودیت datetime-local) در CLAUDE.md بخش «نکات عملیاتی همیشگی» هم ثبت شدن.

### بعد از فاز — پیاده‌سازی «تور آموزشی سایت» از لیست کارهای درخواستی

آیتم دوم لیست «کارهای درخواستی در صف» (CLAUDE.md).

- `npm install driver.js` (سبک، بدون وابستگی اضافه؛ v1.8.0، API تابعی `driver({...}).drive()`).
- `frontend/src/lib/onboarding-tour.ts` — `startOnboardingTour()` مراحل تور رو تعریف و اجرا می‌کنه (۶ مرحله: لوگو، رویدادها، ایجاد رویداد، رویدادهای من، بلیط‌های من، ورود — همه فارسی، دکمه‌های بعدی/قبلی/پایان هم فارسی)؛ `startOnboardingTourIfFirstVisit()` قبلش `localStorage["royaevent_tour_completed"]` رو چک می‌کنه. علامت‌گذاری «دیده‌شده» در callback `onDestroyed` انجام می‌شه (نه `onDestroyStarted` — اون یکی برای کنترل/لغو مقصده، نه side effect، اولین تلاش اشتباه بود و اصلاح شد).
- `components/OnboardingTour.tsx` — کامپوننت client بدون خروجی UI (`return null`)، فقط یک `useEffect` که با یه تأخیر کوچیک (۶۰۰ میلی‌ثانیه، برای اطمینان از رندر کامل هدر) `startOnboardingTourIfFirstVisit()` رو صدا می‌زنه. یک‌بار در `app/layout.tsx` رندر می‌شه.
- `SiteHeader.tsx` به client تبدیل شد (`"use client"` اضافه شد) تا بتونه دکمه‌ی آیکون «راهنمای سایت» (`CircleHelp` از lucide-react) رو با `onClick={startOnboardingTour}` نگه داره — این دکمه صرف‌نظر از `localStorage` همیشه در دسترسه، طبق نیازمندی «قابل تکرار دستی».
- مراحل تور روی `id`های ثابت روی لینک‌های هدر (`#tour-logo`, `#tour-events`, `#tour-create`, `#tour-mine`, `#tour-tickets`, `#tour-login`) سوار می‌شن.
- **RTL polish:** استایل پیش‌فرض `driver.css` فرض LTR داره (دکمه‌ی بستن گوشه‌ی راست‌بالا، ترتیب دکمه‌های ناوبری از راست به چپ). چون popover رو مستقیم در `document.body` می‌سازه (نه داخل درخت React)، CSS Modules روش کار نمی‌کنه؛ به‌جاش با `popoverClass: "roya-tour-popover"` یه کلاس سراسری بهش اضافه شد و override در `globals.css` نوشته شد (دکمه‌ی بستن → چپ، `flex-direction: row-reverse` روی فوتر و دکمه‌های ناوبری).
- راستی‌آزمایی: `npm run build`/`eslint` تمیز؛ HTML خروجی SSR صفحه‌ی اصلی چک شد که همه‌ی `id`های تور و دکمه‌ی «راهنمای سایت» درست رندر می‌شن. تست تعاملی واقعی مرورگر انجام نشد (Playwright هنوز نصب نیست، دام #۸ در CLAUDE.md).

### بعد از فاز — TLS/Docker (تکمیل آیتم سوم لیست کارهای درخواستی) + شکاف‌های UI کشف‌شده حین تست زنده

**TLS/Docker:**
- `backend/Dockerfile` (`python:3.12-slim`، بدون `apt-get build-essential` — تست شد که همه‌ی وابستگی‌ها manylinux wheel دارن، نیازی به کامپایلر نیست)، `frontend/Dockerfile` (multi-stage با `output:"standalone"` در `next.config.ts`، build arg برای `NEXT_PUBLIC_API_BASE_URL` چون این متغیر باید build-time جاسازی بشه نه runtime). هر دو ایمیج واقعاً build شدن و موفق بودن (بک‌اند ۲۲۶ ثانیه، بدون خطا).
- `infra/docker-compose.prod.yml`: nginx (تنها سرویس با پورت عمومی ۸۰/۴۴۳)، certbot (فقط `profiles:["tools"]`، دستی/کرون صدا زده می‌شه، نه سرویس همیشه‌روشن — چون بدون docker socket نمی‌تونه nginx رو بعد از تمدید reload کنه)، backend، frontend، redis، mongo، minio (سناریوی جایگزین object storage). `infra/nginx/conf.d/royaevent.conf` (ریدایرکت اجباری HTTP→HTTPS، HSTS، `client_max_body_size 35M` برای آپلود کلیپ). `infra/renew-certs.sh` برای کرون هاست.
- راهنمای کامل قدم‌به‌قدم (چرا باید گواهی رو با `--standalone` **قبل از** بالا آوردن nginx گرفت، وگرنه nginx اصلاً بالا نمی‌آد چون فایل گواهی وجود نداره) در `docs/deployment_tls.md`.
- **دام واقعی کشف‌شده:** `requirements.txt` داشت `chromadb`/`sentence-transformers` رو uncommented نگه می‌داشت (با یه کامنت که می‌گفت «لازم نیست نصب بشه» ولی خط خودش کامنت نشده بود) — نه تو venv محلی نصب بودن نه جایی import می‌شدن، فقط باعث می‌شدن هر `pip install`/Docker build چند صد مگابایت wheel CUDA/torch غیرضروری دانلود کنه و روی شبکه‌ی ناپایدار این محیط با خطای `THESE PACKAGES DO NOT MATCH THE HASHES` fail بشه. کامنت شدن (فاز ۴ که واقعاً شروع شد، uncomment بشن).

**شکاف‌های UI که فقط با تست زنده‌ی خود کاربر پیدا شدن:**
- **رفرش خودکار access token منقضی‌شده (نه فقط موقع لود صفحه):** access token فقط ۱۵ دقیقه اعتباره؛ `SessionBootstrap` قبلاً فقط موقع لود اولیه تازه‌ش می‌کرد، پس فرم‌های طولانی (مثل ایجاد رویداد با چند جلسه) بعد از ۱۵ دقیقه با «توکن نامعتبر یا منقضی‌شده» fail می‌کردن. فیکس: `refreshAccessToken()` تو `lib/api-client.ts` منتقل شد (نه دیگه تو `SessionBootstrap` تکراری)، و `request()`/`uploadFileWithProgress()` هردو روی پاسخ ۴۰۱ (فقط وقتی `accessToken` واقعاً پاس داده شده بود) یک‌بار خودکار توکن رو تازه و درخواست اصلی رو تکرار می‌کنن. `SessionBootstrap` هم به همون تابع مشترک refactor شد تا فقط یک guard تک‌پرواز (نه دوتای ناهماهنگ) در کل اپ وجود داشته باشه — جزئیات ریسک race condition در دام #۱۵ (CLAUDE.md).
- **بدون UI برای مدیریت انواع بلیط:** بک‌اند از فاز ۳ `POST /events/{id}/ticket-types` رو داشت، ولی هیچ صفحه‌ی فرانتی برای برگزارکننده وجود نداشت که ازش استفاده کنه — یعنی رویدادهای واقعی که کاربر می‌ساخت هیچ بلیطی نداشتن و تو صفحه‌ی رویداد پیام «هنوز بلیطی تعریف نشده» می‌دیدن. صفحه‌ی جدید `app/(organizer)/organizer/events/[id]/tickets/page.tsx` اضافه شد (فرم افزودن نوع بلیط + لیست بلیط‌های موجود)، لینک از «رویدادهای من» و از صفحه‌ی موفقیت بعد از ایجاد رویداد (با یادآوری صریح که بدون حداقل یک بلیط، انتشار بی‌فایده‌ست).
- **بدون راه ویرایش بنر/کلیپ بعد از رد‌کردن مرحله‌ی اولیه یا بعد از انتشار:** صفحه‌ی جدید `app/(organizer)/organizer/events/[id]/media/page.tsx` — همون منطق آپلود create/page.tsx (دکمه‌ی سفارشی + progress + پیش‌نمایش) ولی برای هر رویدادی (پیش‌نویس یا منتشرشده) در هر زمانی، با fetch اولیه‌ی رویداد بر اساس id.
- **دکمه‌های آپلود native (`<input type="file">` خام) نامفهوم بودن و متن انگلیسی مرورگر («Choose File») نشون می‌دادن** — تو یه سایت کاملاً فارسی/RTL خیلی به چشم می‌اومد. فیکس: input واقعی با `className="hidden"` مخفی شد، یه `Button` فارسی («انتخاب فایل بنر»/«جایگزینی بنر») با `ref.current?.click()` جایگزینش شد، و اسم فایل انتخابی کنارش نشون داده می‌شه. یه پاراگراف راهنما هم بالای بخش آپلود اضافه شد چون بدون توضیح، کاربر اصلاً نمی‌فهمید این مرحله اختیاریه و بعد از «ایجاد رویداد» ظاهر می‌شه.
- **بدون فیلتر/جستجو در لیستینگ عمومی رویدادها:** بک‌اند از فاز ۲ `category_id`/`format` رو به‌عنوان query param پشتیبانی می‌کرد ولی هیچ UI ای بهش وصل نبود. `components/EventsFilter.tsx` (Select دسته‌بندی + نوع برگزاری، با `useSearchParams`/`router.push` برای sync با URL) به `app/events/page.tsx` اضافه شد؛ صفحه به async `searchParams` مجهز شد. **جستجوی متنی آزاد هنوز نیست** — اون بخشیه از فاز ۴ (ChromaDB) که هنوز شروع نشده.
- **بدون صفحه‌ی «علاقه‌مندی‌های من»:** دکمه‌ی FavoriteButton از قبل رو صفحه‌ی رویداد بود و toggle می‌کرد، ولی جایی برای دیدن لیست نتیجه نبود. `app/favorites/page.tsx` اضافه شد (همون الگوی `/tickets`، `socialApi.myFavorites()`)، لینک تو هدر.
- **اسم روزهای هفته‌ی تقویم شمسی خیلی کوتاه/ناخوانا بود:** جزئیات کامل در دام #۱۴ (CLAUDE.md) — `weekDays` صریح override شد، عرض تقویم زیاد شد.

## نکات/دام‌های این فاز

- **برای تست early-bird:** برای شبیه‌سازی «بازه‌ی زودهنگام گذشته»، `published_at` رو با `utcnow() - timedelta(days=N)` (گذشته‌ی واقعی) عقب ببر، نه با تفریق کسری از `starts_at` — اون روش اول باعث شد `published_at` به آینده بره (باگ در خود تست، نه در `ticket_service`) و تست اشتباهی pass/fail می‌داد.
- **Next.js App Router الزام می‌کنه همه‌ی route های هم‌سطح روی یک segment، اسم پارامتر dynamic یکسانی داشته باشن** (چون route groups مثل `(organizer)` در URL نامرئی‌ان). یک بار `app/(organizer)/events/[id]/attendees/` با `app/events/[slug]/` تصادم کرد (هر دو روی `/events/*` می‌شینن) و کل `next dev` با خطای `You cannot use different slug names for the same dynamic path` کرش کرد. فیکس: مسیر داشبورد شرکت‌کنندگان رو بردیم زیر `/organizer/events/[id]/attendees` (هم‌راستا با namespace بک‌اند). قبل از افزودن هر route جدید با پارامتر dynamic، چک کن آیا segment هم‌نامش جای دیگه با اسم پارامتر متفاوت قبلاً تعریف شده.
- **دانلود فایل (مثل CSV export) که نیاز به `Authorization: Bearer` داره رو نمی‌شه با `<a href>` مستقیم زد** — چون مرورگر هیچ header دلخواهی به ناوبری معمولی اضافه نمی‌کنه و access token عمداً در کوکی نیست. راه‌حل: `fetch` با header دستی، گرفتن `blob()`، `URL.createObjectURL` و کلیک برنامه‌ای روی یک `<a>` موقت (`organizer-api.ts: downloadAttendeesCsv`).
- سرور uvicorn بدون `--reload` بعد از هر تغییر کد بک‌اند دستی باید restart بشه — یک بار بعد از اضافه‌کردن fallback به `organizer_name`، فراخوانی API همچنان نتیجه‌ی قدیمی برمی‌گردوند چون پردازه‌ی از قبل بالا کد رو در حافظه داشت.
- یه داده‌ی تستی (عنوان رویداد) با متن فارسی مستقیم در آرگومان `curl -d` روی Git Bash ویندوز مخدوش شد (`??????`) — رفع شد با پیلود UTF-8 فایل + `curl --data-binary`. جزئیات کامل این دام در CLAUDE.md بخش نکات عملیاتی همیشگی ثبت شده (نه اینجا، چون هر فازی ممکنه دوباره پیش بیاد).

## راستی‌آزمایی

بک‌اند و فرانت هر دو real dev server (API=8000, Next=3000)، دسته‌بندی‌ها seed شدن، از طریق OTP واقعی (دو کاربر: برگزارکننده + خریدار) لاگین شد، یک رویداد واقعی ساخته/publish شد با دو نوع بلیط (رایگان/پولی) و یک کد تخفیف، و کل چرخه‌ی فاز ۳ (favorite، follow organizer، create+complete order با تخفیف، calendar-link، لیست/CSV export شرکت‌کنندگان، cancel registration) مستقیماً روی سرور واقعی با `curl` تست شد — همه‌چیز درست کار کرد. HTML خروجی SSR صفحه‌ی جزئیات رویداد هم بررسی شد (RTL/فارسی، organizer_name، ticket checkout wire شده در RSC payload).

## Commitهای مرتبط

`d4120b7` (بک‌اند checkpoint بدون تست)، `f044e20` (تست‌ها)، `c0d7226` (organizer_name/me-follows/کد رویداد RE-)، `9a1e057` (فرانت)، `814b06b` (docs)، `b2dd081` (فیکس لوگوی هدر)، `6926eec` (تم تیره‌ی دائمی سایت)
