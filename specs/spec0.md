# فاز ۰ — Scaffolding و مستندات

وضعیت: ✅ کامل و commit‌شده.

> این اولین فاز است؛ خلاصه‌ای از فازهای قبل وجود نداره.

## هدف

اسکلت اولیه‌ی مونوریپو (backend/frontend)، سرویس‌های جانبی dev (docker-compose)، و مستندسازی پایه — قبل از شروع هر منطق تجاری.

## چیزی که ساخته شد

- **بک‌اند:** اسکلت FastAPI با `GET /health` (ساده، ۲۰۰ برمی‌گردونه).
- **فرانت‌اند:** اسکلت Next.js (App Router) + shadcn/ui + Tailwind، با `dir="rtl" lang="fa"` روی `<html>` از همون ابتدا، و فونت Kalameh محلی (`next/font/local`).
- **infra:** `infra/docker-compose.yml` با Redis, Mongo, MinIO, Loki, Prometheus, Grafana — همه‌ی سرویس‌های جانبی dev در یک فایل.
- **CI پایه:** GitHub Actions اسکلت (تست بک‌اند + build/lint فرانت).
- **مستندات:** `docs/architecture.md` (پلن کامل معماری، مرجع اصلی تصمیمات فنی)، `docs/event_otp_email_sms_plan_fa.md` (سند اولیه‌ی OTP که کاربر نوشته بود، منتقل‌شده به `docs/` بدون تغییر)، `data/eseminar.tv/analysis.md` و `data/evand.com/analysis.md` (تحلیل رقبا).

## تصمیم‌ها

- فونت Kalameh (`fontiran.com`) **تجاری/مالکیتی** است و کد لایسنس ۶رقمی‌اش پر نشده. کاربر صریحاً گفته با همین حال فایل‌ها رو نگه دار و ریپو رو public کن — تصمیم آگاهانه‌ی کاربره، در فازهای بعد دوباره ازش سؤال نشد. پوشه‌ی خام `/font/` (سورس اصلی وندور) در `.gitignore` است و کامیت نمی‌شه؛ فقط `frontend/src/fonts/kalameh/*.woff2` (فایل‌های واقعاً استفاده‌شده) کامیت شدن.

## راستی‌آزمایی

- `docker compose -f infra/docker-compose.yml up -d` بدون خطا بالا اومد.
- `curl localhost:8000/health` پاسخ ۲۰۰ داد.
- `data/eseminar.tv/analysis.md` و `data/evand.com/analysis.md` موجود و کامل بودن.

## نکات/دام‌های این فاز

- یک `package.json`/`node_modules/` ناخواسته (پکیج `agentation`) در ریشه‌ی ریپو (نه داخل `frontend/`) توسط ابزار محیط ساخته شد، ربطی به پروژه نداره — در `.gitignore` مستثنا شد (`/node_modules/`, `/package.json`, `/package-lock.json` با `/` پیشرو یعنی فقط ریشه، نه `frontend/`). اگه دوباره دیدیش، پاکش نکن با دستکاری دستی، همون gitignore کافیه.

## Commitهای مرتبط

`b0a5022` (اسکلت بک‌اند)، `3c9aa57` (اسکلت فرانت)، `82c0eb8` (docker-compose + CI)
