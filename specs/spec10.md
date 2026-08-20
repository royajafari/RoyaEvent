# فاز ۱۰ — تقویت تست + مقاومت آفلاین/RTL

وضعیت: ✅ کامل (بک‌اند + فرانت)، تست‌شده، لینت/بیلد تمیز.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن. فاز ۴: جستجوی معنایی + صفحه‌ی اصلی. فاز ۵: پنل ادمین. فاز ۶: صف اعلان‌ها. فاز ۷: امتیاز/نظر ۴محوره. فاز ۸: آنالیتیکس/KPI. فاز ۹: استک مانیتورینگ (Prometheus/Loki/Grafana). جمعاً ۳۱۲ تست بک‌اند پاس، صفر تست فرانت، تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec9.md`](spec9.md).

## هدف

بخش فاز ۱۰ نقشه‌ی راه («تقویت تست + مقاومت/RTL») + بخش ۱۲ `docs/architecture.md` (نیازمندی ۳۳، الگوی مقاومت در برابر قطع اتصال): پوشش تست بک‌اند رو روی نقاط ریسک واقعی (نه فقط تعداد) عمیق‌تر کن، اولین زیرساخت تست فرانت این پروژه رو بساز، الگوی آفلاین/reconnect مستندشده رو پیاده کن، یک ErrorBoundary سراسری اضافه کن، و یک ممیزی RTL واقعی (نه فرضی) روی کد انجام بده.

## چیزی که ساخته شد

### بک‌اند — تقویت تست

- `pytest-cov` واقعاً نصب و اجرا شد (قبلاً در `requirements.txt` بود ولی در venv محلی نصب نشده بود — گزارش پوشش واقعی هیچ‌وقت لوکال دیده نشده بود). پوشش اولیه: **۹۰٪**.
- تست‌های مستقیم و جدید برای نقاط کم‌پوشش/امنیتی واقعی (نه حدسی — بر اساس `--cov-report=term-missing`):
  - `tests/unit/test_rate_limit.py` (جدید): `enforce_cooldown`، `enforce_otp_request_limits` (سقف destination + سقف مستقل per-user)، و `rate_limit_key` (کاربر لاگین‌شده → `user:{id}`، مهمان → `ip:...`، توکن جعلی/نامعتبر → بی‌صدا fallback به `ip:...`) — این ماژول‌ها قبلاً **هیچ تست اختصاصی** نداشتن، فقط یک فیکسچر `_reset_rate_limiter` که state رو بین تست‌ها ریست می‌کرد.
  - `tests/unit/test_deps.py` (جدید): `get_current_user_optional` با توکن نامعتبر → `None` برمی‌گردونه (نه ۴۰۱، برخلاف `get_current_user`).
  - `tests/unit/test_auth_service.py`: ۵ تست جدید — refresh با JWT معتبر ولی هیچ ردیف matching در DB (فرق با «فرمت نامعتبر»)، refresh با ردیف منقضی‌شده، **refresh توسط کاربر تعلیق‌شده** (سومین جای قاعده‌ی «سه جای auth flow» در CLAUDE.md که قبلاً تست مستقیم نداشت)، access token جعلی، access token برای کاربر حذف‌شده.
  - `tests/unit/test_otp_service.py`: ۳ تست جدید — `verify_otp`/`resend_otp` با `challenge_id` ناموجود، و مسیر دفاعی «attempt_count از قبل >= max_attempts ولی status هنوز PENDING» (حالتی که در جریان عادی سرویس رخ نمی‌ده چون status همون لحظه LOCKED می‌شه، ولی کد باید در برابرش مقاوم بمونه).
  - پوشش نهایی: **۹۱٪** (۳۲۹ تست). `rate_limit.py`/`rate_limit_middleware.py`/`auth_service.py`/`otp_service.py` هرکدوم به ۱۰۰٪ رسیدن.
- CI (`--cov-fail-under=85`) اضافه شد تا افت پوشش در آینده silent نمونه (فاصله‌ی امن از ۹۱٪ فعلی، برای فایل‌های provider که ذاتاً کم‌پوشش‌ان — نگاه کن به نکات پایین).

### فرانت‌اند — زیرساخت تست (اولین بار)

- **Vitest + `@vitejs/plugin-react-swc` + `@testing-library/react` + `@testing-library/jest-dom`** — نه Jest (سازگاری بهتر با Next.js 16/Turbopack و بدون کانفیگ اضافه)، نه `@vitejs/plugin-react` معمولی (کانفلیکت peer dependency واقعی، نگاه کن به نکات پایین). `frontend/vitest.config.ts` + `vitest.setup.ts` (matcher های jest-dom) + script `npm test`.
- تست واحد برای منطق خالص (بدون رندر کامپوننت — نقطه‌ی شروع کم‌ریسک‌ترین): `lib/digits.test.ts`، `lib/calendar.test.ts`، `lib/date.test.ts`.
- CI فرانت یک step تست جدید گرفت (بین lint و build).

### فرانت‌اند — مقاومت آفلاین (نیازمندی ۳۳ architecture.md)

- **`hooks/useNetworkStatus.ts`**: ترکیب رویداد `online`/`offline` مرورگر + پینگ دوره‌ای هر ۱۵ ثانیه به `/health` (بک‌اند، نه `/api/v1/health` — بیرون از prefix است). چرا پینگ لازمه نه فقط رویداد مرورگر: `navigator.onLine` فقط یعنی «به یک شبکه وصلی»، نه «سرور ما واقعاً در دسترسه».
- **`components/NetworkStatusGate.tsx`** (در `layout.tsx`، دور `SiteHeader`/`{children}`/`SiteFooter`): دو رفتار طبق spec —
  - کاربر لاگین‌کرده: هیچ UI بلاک‌کننده‌ای نشون نمی‌ده؛ فقط بعد از یک transition واقعی آفلاین→آنلاین، `refreshAccessToken()` (همون promise تک‌پرواز `lib/api-client.ts`) رو صدا می‌زنه؛ اگه شکست خورد (یعنی کوکی رفرش‌توکن هم در این فاصله منقضی/باطل شده) به `/login` می‌فرسته.
  - کاربر مهمان: اسکلت تمام‌صفحه («در حال اتصال مجدد به اینترنت...») تا اتصال واقعی برقرار بشه.
- **۵ تست واحد** (`hooks/useNetworkStatus.test.ts`، با `fetch` مقلد): وضعیت اولیه، شکست health-check با وضعیت غیر-ok، شکست کامل fetch (قطعی واقعی شبکه)، واکنش فوری به رویداد `offline`، پینگ تازه روی رویداد `online`.

### فرانت‌اند — ErrorBoundary سراسری

- **`app/error.tsx`** (segment error boundary خودکار نکست‌جس، نه یک کلاس دستی) + **`app/global-error.tsx`** (برای کرش خود root layout، خودش `<html>`/`<body>` کامل داره چون کل layout رو جایگزین می‌کنه). خطای شبکه‌ای رو از خطای رندر واقعی جدا می‌کنه (`isLikelyNetworkError`، تست‌شده در `app/error.test.ts`، اکسپورت‌شده برای تست مستقیم) — پیام و اقدام پیشنهادی فرق داره.

### فرانت‌اند — ممیزی RTL (بر اساس بررسی کد، نه مرورگر واقعی)

چون دانلود Chromium/Playwright در این محیط با ۴۰۳ جغرافیایی مسدوده (نکته‌ی همیشگی CLAUDE.md #۸)، ممیزی صرفاً code-review بود، نه بصری. یافته‌های واقعی و رفع‌شده:

- **`components/ui/select.tsx`**: `SelectValue` پیش‌فرض `text-left` داشت (نه `text-right`) — روی هر `Select` سایت (فیلتر رویدادها، پنل ادمین، فرم ایجاد/ویرایش رویداد، مدیریت بلیط) متن انتخاب‌شده به‌جای راست، چپ‌چین می‌شد. یک تغییر در primitive مشترک، رفع در همه‌جا.
- **اعداد خام (raw ASCII) در جاهایی که از دورهای قبلی فیکس دیجیت فارسی (CLAUDE.md #۹) جا مونده بودن** — همه‌شون فقط دور `toPersianDigits()` پیچیده شدن: شماره‌ی ردیف در همه‌ی ۷ جدول پنل ادمین (`admin/page.tsx`)، امتیاز نظر (`{r.overall_computed.toFixed(1)} / ۵`)، میانگین امتیاز رویداد/مدرس/برگزارکننده (`EventCard.tsx`، `events/[slug]/page.tsx`، `RateEntityWidget.tsx` — چون `.toFixed()` خودش هیچ‌وقت لوکالایز نمی‌کنه، برخلاف `.toLocaleString("fa-IR")`)، شماره‌ی جلسه (`TicketCheckout.tsx`، `events/[slug]/page.tsx`)، درصد کد تخفیف (`TicketCheckout.tsx` — شاخه‌ی مبلغ ثابت کنارش درست بود، شاخه‌ی درصدی نه)، ظرفیت بلیط (`organizer/.../tickets/page.tsx`).
- **بررسی شد، مشکلی نبود** (برای این‌که دوباره کسی وقتش رو صرف نکنه): آیکون‌های جهت‌دار کاروسل (`EventCarousel.tsx`/`CategoryCarousel.tsx` — قبلاً درست پیاده شده بودن، دکمه‌ی «بعدی» با `ChevronLeft` سمت چپ، «قبلی» با `ChevronRight` سمت راست)، ادغام `html5-qrcode` (فقط از کلاس سطح‌پایین `Html5Qrcode` استفاده می‌کنه، نه UI انگلیسی `Html5QrcodeScanner`)، `react-multi-date-picker` (حالت RTL خودکار از روی اسم locale `persian_fa` فعال می‌شه).

## نکات/دام‌های این فاز

- **`@vitejs/plugin-react` (نسخه‌ی معمول، babel-based) نصبش fail شد** — کانفلیکت peer dependency واقعی بین `@babel/core@8` (که این پلاگین transitively می‌خواد) و `@babel/core@^7` (که `shadcn` از قبل نصب کرده). راه‌حل: `@vitejs/plugin-react-swc` به‌جاش — SWC-based، دقیقاً همون transformی که خود Next.js استفاده می‌کنه، بدون هیچ وابستگی به Babel.
- **pool پیش‌فرض Vitest (`forks`، بر پایه‌ی `child_process`) تو این محیط (ساندباکس ویندوز) گیر می‌کنه و timeout می‌ده** (`Timeout waiting for worker to respond`) — بدون هیچ خطای واضح دیگه‌ای. `pool: "threads"` (بر پایه‌ی `worker_threads`، نه پردازه‌ی جدا) تو `vitest.config.ts` قابل‌اعتماد و سریع‌تره؛ برای تست‌های این پروژه هیچ ریسکی هم نداره چون به ایزوله‌سازی سطح پردازه نیازی نیست.
- **باگ واقعی کشف‌شده حین ساخت `useNetworkStatus`: hydration mismatch.** خوندن مستقیم `navigator.onLine` داخل خود `useState` initializer (`useState(() => navigator.onLine)`) باعث می‌شد سرور (که `navigator` اصلاً نداره، پس همیشه `true`) با اولین رندر کلاینت (که ممکنه واقعاً `navigator.onLine === false` ببینه) فرق کنه — خطای hydration واقعی که در لاگ dev سرور دیده شد، نه فرضی. راه‌حل درست: مقدار اولیه همیشه `true` (چه سرور چه کلاینت)، مقدار واقعی فقط داخل `useEffect` (که فقط بعد از hydrate اجرا می‌شه) با `checkHealth()` تصحیح می‌شه — که هم دقیق‌تره (واقعاً سرور رو چک می‌کنه، نه فقط یه API مرورگری غیرقابل‌اعتماد) هم امن برای SSR.
- **الگوی امن `react-hooks/set-state-in-effect` برای async polling (نه فقط فراخوانی import‌شده از ماژول دیگه، نکته‌ی #۱۹ CLAUDE.md که قبلاً مستند شده بود)**: یک تابع async محلی که بعد از `await` مستقیم setState صدا بزنه، حتی وقتی از دل effect صدا زده بشه، فلگ می‌شه. ولی یک تابع **غیر-async** که به‌جای `await` از زنجیره‌ی `.then()/.catch()` استفاده می‌کنه، فلگ نمی‌شه — این الگو از قبل تو `app/tickets/page.tsx: loadTickets` وجود داشت (تأییدشده lint-clean)؛ `useNetworkStatus.ts: checkHealth` عمداً از همون الگو (نه `async function`) استفاده کرد.
- **`npm ci` در CI با Node 20 fail کرد ولی `npm ci`/`npm install` محلی (Node 24) مشکلی نداشت** — `package-lock.json` با npm 11.16.0 (محیط dev) نوشته شده بود و npm 10.8.2 (همراه Node 20 در CI) فرمتش رو کامل نمی‌فهمید (`Missing: @swc/helpers@... from lock file`). چند وابستگی جدید این فاز (`jsdom@30`, `@testing-library/jest-dom@7`) هم صراحتاً `engines: {node: ">=22"}` می‌خوان. رفع: node-version در `ci.yml` از `"20"` به `"24"` (هم‌راستا با محیط dev واقعی، نه یک نسخه‌ی «پایدار» عقب‌تر — همون فلسفه‌ی نکته‌ی #۲۳ CLAUDE.md برای وابستگی‌های پایتون).
- **اجرای `npm run build` درحالی‌که `npm run dev` هم‌زمان بالا بود، دوباره `.next/` رو خراب کرد** (دقیقاً نکته‌ی #۱۷ CLAUDE.md) — با kill کردن دستی پردازه‌ی dev (پیداشده از روی `netstat`/پورت ۳۰۰۰)، `rm -rf .next`، و ری‌استارت رفع شد؛ بعد از ری‌استارت، لاگ dev سرور واقعاً برای کشف باگ hydration بالا استفاده شد.
- **ممیزی RTL بدون مرورگر واقعی (۴۰۳ جغرافیایی روی Chromium) کاملاً ممکنه، فقط باید code-review-محور باشه**: بررسی مستقیم منطق کتابخونه‌های شخص‌ثالث (`node_modules/react-multi-date-picker`، `node_modules/html5-qrcode`) به‌جای فرض‌کردن، چند false-positive رو رد کرد (مثلاً کاروسل‌ها که ادعا می‌شد جهتشون اشتباهه، در واقع درست بودن).

## راستی‌آزمایی

- بک‌اند: `ruff check .` تمیز، `pytest --cov=app --cov-fail-under=85` → **۳۲۹ تست پاس، ۹۱٪ پوشش**.
- فرانت: `npx eslint src` تمیز، `npm run test` (Vitest) → **۲۶ تست پاس**، `npm run build` موفق (شامل بررسی نوع TypeScript کامل).
- سرور dev واقعی: بعد از فیکس hydration، `GET /` بدون هیچ خطای hydration/console در لاگ سرور — با `curl` + بررسی لاگ خام تأیید شد (نه اسکرین‌شات مرورگر واقعی، طبق محدودیت شناخته‌شده‌ی این محیط).
- CI (`gh run watch`) سبز — هر دو job (`backend`/`frontend`) روی هر پوش.

## Commitهای مرتبط

(در همین نشست کامیت شدن — نگاه کن به تاریخچه‌ی گیت برای هش دقیق: تقویت تست بک‌اند، زیرساخت تست فرانت + مقاومت آفلاین + ErrorBoundary، فیکس Node.js نسخه‌ی CI، فیکس‌های RTL.)
