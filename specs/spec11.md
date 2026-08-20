# فاز ۱۱ — آماده‌سازی دیپلوی VPS

وضعیت: ⏳ در جریان (نه کامل) — بخش TLS/Docker/مانیتورینگ کد و محلی تست شد؛ منتظر VPS واقعی + provider ایمیل/پیامک ایرانی.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰ تا ۱۰ کامل — نگاه کن به [`spec0.md`](spec0.md)…[`spec10.md`](spec10.md). بک‌اند ۳۲۹ تست پاس (پوشش ۹۱٪)، فرانت Vitest+RTL+build تمیز. بخش TLS/Nginx/Docker این فاز از قبل (مستقل از ترتیب فازها) انجام شده بود — `docs/deployment_tls.md` و `specs/spec3.md`.

## هدف این نشست

تکمیل باقی‌مانده‌ی فاز ۱۱: افزودن سرویس `worker` (که کلاً از `docker-compose.prod.yml` جا افتاده بود) + استک مانیتورینگ production، و راه‌اندازی provider واقعی ایمیل/پیامک برای کاربر ایرانی.

## چیزی که ساخته شد

### `infra/docker-compose.prod.yml`

- **سرویس `worker` جدید** — یافته‌ی واقعی این نشست: تا الان این فایل اصلاً سرویس worker نداشت، یعنی در یک دیپلوی واقعی production، صف اعلان (`notification_outbox`)، اسکنر یادآوری ۱ساعته، و رول‌آپ شبانه‌ی KPI هیچ‌وقت واقعاً dispatch نمی‌شدن (فقط enqueue می‌شدن، چون backend اصلی فقط request-time کار می‌کنه). همون ایمیج backend رو reuse می‌کنه (`build: context: ../backend`)، فقط `command` فرق داره: `sh -c "alembic upgrade head && python -m app.workers.scheduler"` — `alembic upgrade head` دوباره اینجا هم لازمه چون `command:` کل CMD ایمیج (که alembic رو قبل از gunicorn می‌زنه) رو override می‌کنه نه اضافه؛ idempotent بودن alembic یعنی صدا زدنش دوباره از دو کانتینر جدا (backend + worker) بی‌ضرره.
- **استک مانیتورینگ** (Loki/Prometheus/Grafana + Promtail) — دقیقاً مثل dev، با این تفاوت‌ها:
  - `prometheus.prod.yml` جدید: scrape target `backend:8000` (سرویس تو همون شبکه) به‌جای `host.docker.internal:8000` (dev، چون بک‌اند dev روی هاست اجراست).
  - همه‌ی سه سرویس (Loki/Prometheus/Grafana) فقط روی `127.0.0.1` پورت دارن، نه public/nginx — دسترسی ادمین با SSH tunnel (`ssh -L 3300:localhost:3300 user@vps-ip`)، نه یک URL عمومی بدون auth اضافه.
  - `GF_SECURITY_ADMIN_PASSWORD` حالا از `${GRAFANA_ADMIN_PASSWORD:?...}` میاد (اجباری در `infra/.env`)، نه هاردکد `admin/admin` مثل dev.
  - Promtail همچنان static file scrape از `./logs` (نه docker service discovery/docker.sock) — طبق همون تصمیم امنیتی که برای certbot هم گرفته شده بود (پرهیز از دسترسی docker socket به کانتینرهای جانبی). برای این‌که این کار کنه، backend و worker هر دو `./logs:/var/log/royaevent` رو mount می‌کنن و `LOG_FILE_PATH` ست می‌شه.

### بک‌اند — لاگ به فایل (علاوه بر stdout)

- `app/core/logging_config.py: setup_json_logging()` پارامتر اختیاری `file_path` گرفت — اگه ست بشه، یه `FileHandler` هم علاوه بر `StreamHandler` اضافه می‌شه (هر دو JSON).
- `Settings.log_file_path: str | None = None` (فقط در production از env ست می‌شه).
- `main.py`/`scheduler.py` هر دو `setup_json_logging(level=..., file_path=settings.log_file_path)` صدا می‌زنن.

### `frontend/Dockerfile` — باگ واقعی کشف و رفع شد

- سه استیج (`deps`/`builder`/`runner`) از `node:22-alpine` استفاده می‌کردن — دقیقاً همون مشکل ریشه‌ای CI که در فاز ۱۰ کشف/رفع شده بود (`npm ci` با npm بسته‌شده به Node 22 نمی‌تونه `package-lock.json` نوشته‌شده با npm 11.16 رو بخونه: `Missing: @swc/helpers@... from lock file`). این‌بار در **build واقعی Docker image production**، نه فقط CI، لو رفت — یعنی قبل از این فیکس، دیپلوی واقعی production همون لحظه‌ی build شکست می‌خورد. هر سه استیج به `node:24-alpine` تغییر کرد (هم‌راستا با فیکس CI فاز ۱۰).

### تست محلی TLS (بدون VPS واقعی)

چون بدون VPS/دامنه‌ی واقعی امکان گواهی Let's Encrypt واقعی نیست، مکانیزم nginx+TLS با یک گواهی **self-signed** برای `localhost` محلی تست شد (نه چیزی که commit بشه — همه‌چیز در یک دایرکتوری scratch موقت):

- `openssl req -x509 ... -subj "/CN=localhost"` → گواهی self-signed.
- کپی موقت `infra/nginx/conf.d/royaevent.conf` با دامنه‌ی `localhost` جایگزین `royaevent.example.com`.
- یک `docker-compose` مجزا (نه فایل واقعی پروژه) که سرویس‌های واقعی `docker-compose.prod.yml` رو با گواهی/nginx‌کانفیگ scratch بالا می‌آورد؛ برای backend/frontend از ایمیج‌های قبلاً build-شده (cache) استفاده شد به‌جای build دوباره — چون build واقعی تو این محیط (شبکه‌ی ناپایدار sandbox) رو backend یک بار **بیش از ۲ ساعت** گیر کرد بدون تموم‌شدن (تأییدشده با `docker buildx history ls`)، همون الگوی شناخته‌شده‌ی دام #۷/#۱۶ CLAUDE.md (پکیج‌های سنگین pip روی این شبکه).
- **نتیجه: مکانیزم کامل تأیید شد** —
  - ریدایرکت HTTP→HTTPS (۳۰۱) ✅
  - handshake TLS موفق + گواهی درست سرو می‌شه (تأییدشده با `openssl s_client`: `subject=CN=localhost`, `issuer=CN=localhost`، دقیقاً همون گواهی self-signed تولیدشده) ✅
  - صفحه‌ی اصلی واقعی از پشت nginx→frontend (۲۰۰، محتوای واقعی) ✅
  - مسیر `/api/` درست به `backend:8000` proxy می‌شه (یک ۴۰۴ روی `/api/v1/home/sections` دیده شد، ولی با curl مستقیم به backend container هم دقیقاً همون ۴۰۴ گرفته شد — یعنی نه یه باگ nginx، فقط ایمیج cache‌شده‌ی قدیمی این route رو نداشت، چون از یک تست build خیلی قدیمی‌تر از فازهای اخیر بود) ✅
- بعد از تست، کل استک/ولوم‌ها/ایمیج throwaway پاک شدن؛ هیچ فایلی به ریپو اضافه نشد.

## نکات/دام‌های این فاز

- **قبل از این نشست، `docker-compose.prod.yml` اصلاً سرویس worker نداشت** — یه gap واقعی که تا حالا کشف نشده بود چون هیچ‌وقت واقعاً روی VPS دیپلوی نشده بودیم. همیشه قبل از اعلام «آماده‌ی دیپلوی»، چک کن هر پردازه‌ی جدا (نه فقط request-time) که در dev لازمه (worker، هر cron/scheduler دیگه) تو compose فایل production هم هست.
- **Brevo کاربر مستقر در ایران رو صریحاً تو ToS ممنوع کرده (بخش OFAC/sanctions)** — کشف‌شده حین تلاش واقعی برای ثبت‌نام. Resend (جایگزین دوم کد) صریحاً ننوشته ولی چون شرکت آمریکاییه همچنان تابع همون قانونه، فقط ریسکش (نسبت به این‌که صراحتاً می‌نویسه یا نه) نامشخص‌تره. تصمیم: provider ایمیل تراکنشی **ایرانی** (نجوا) — هنوز در کد پیاده نشده، چون مستندات فنی API واقعی‌شون تو صفحات عمومی موجود نیست (فقط بعد از تیکت پشتیبانی/فعال‌سازی در دسترس می‌شه). Kavenegar (پیامک، از قبل تو کد آماده) این مشکل رو نداره چون از اول شرکت ایرانیه.
- **دلیل واقعی build چند-ساعته‌ی backend (نه فقط کند)**: `docker buildx history ls` نشون داد build روی ۲ ساعت گیر کرده بود (`Running 119m 30s+`) — تأیید شد این «کند» نیست، واقعاً stuck/hang روی دانلود شبکه‌ست (torch/chromadb سنگین). راه‌حل عملی برای تست‌های محلی مشابه در آینده: به‌جای build دوباره، از ایمیج‌های cache‌شده‌ی قبلی (`docker images`) استفاده کن اگه فقط مکانیزم زیرساخت (نه کد اپ) رو می‌خوای تست کنی.
- **برای بررسی این‌که یه ۴۰۴/خطا از nginx میاد یا از upstream خودش**، همیشه همون درخواست رو مستقیم به سرویس backend (بدون واسطه‌ی nginx، مثلاً با `docker exec` از یه کانتینر دیگه‌ی همون شبکه) هم بزن — اگه نتیجه یکی بود، nginx بی‌گناهه.

## راستی‌آزمایی

- بک‌اند: `pytest -q` → ۳۲۹ تست پاس (بدون تغییر نسبت به فاز ۱۰، چون تغییرات این فاز فقط زیرساخت/config بودن)، `ruff check .` تمیز.
- `docker compose -f infra/docker-compose.prod.yml config` با env نمونه سینتکسش معتبره.
- تست محلی TLS بالا — کامل موفق (به‌جز یک ۴۰۴ توضیح‌داده‌شده که مال ایمیج cache قدیمیه، نه کد فعلی).

## باقی‌مانده (خارج از کنترل این نشست)

- VPS واقعی + دامنه (کاربر در حال خرید).
- کلید API واقعی نجوا (ایمیل) — منتظر جواب تیکت پشتیبانی.
- کلید API واقعی Kavenegar (پیامک) — کاربر در حال ثبت‌نام.
- نوشتن provider نجوا در کد (`app/providers/email/najva.py`) — بعد از دریافت مستندات API واقعی.
- استراتژی بکاپ (SQLite + MinIO + Mongo) — هنوز مستند نشده، بعد از VPS واقعی برنامه‌ریزی می‌شه.

## Commitهای مرتبط

(در همین نشست کامیت می‌شه — نگاه کن به تاریخچه‌ی گیت برای هش دقیق.)
