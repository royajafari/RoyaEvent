# رویا ایونت (RoyaEvent)

پلتفرم مدیریت و تجربه‌ی رویداد/وبینار، فارسی‌زبان و کاملاً RTL — مشابه eseminar.tv و evand.com با قابلیت‌های اضافه (امتیازدهی چندمحوره، پنل ادمین کامل، آنالیتیکس پشت‌صحنه).

## معماری و مستندات

- پلن کامل معماری/فازبندی: [`docs/architecture.md`](docs/architecture.md) *(به‌زودی تکمیل می‌شود)*
- طراحی OTP/Email/SMS: [`docs/event_otp_email_sms_plan_fa.md`](docs/event_otp_email_sms_plan_fa.md)
- تحلیل رقبا: [`data/eseminar.tv/analysis.md`](data/eseminar.tv/analysis.md) و [`data/evand.com/analysis.md`](data/evand.com/analysis.md)

## استک فنی

| لایه | فناوری |
|---|---|
| فرانت‌اند | Next.js (App Router) + shadcn/ui + Tailwind، RTL/فارسی |
| بک‌اند | FastAPI (Python) |
| دیتابیس اصلی | SQLite (WAL mode) |
| آنالیتیکس رفتاری | MongoDB |
| کش/Rate-limit | Redis |
| ذخیره‌سازی فایل | MinIO |
| جستجوی محتوایی | ChromaDB (embedded) |
| احراز هویت | OTP (SMS: IPPanel/Kavenegar، Email: Brevo/Resend) + JWT |
| مانیتورینگ | Loki + Prometheus + Grafana |

## پیش‌نیازها

- Node.js ≥ 20، npm
- Python ≥ 3.12
- Docker + Docker Compose

## راه‌اندازی محیط توسعه

```bash
# ۱) سرویس‌های جانبی
docker compose -f infra/docker-compose.yml up -d

# ۲) بک‌اند
cd backend
python -m venv .venv
.venv/Scripts/activate   # ویندوز؛ در لینوکس/مک: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # و مقادیر لازم رو پر کنید
uvicorn app.main:app --reload

# ۳) فرانت‌اند
cd frontend
npm install
npm run dev
```

- بک‌اند: http://localhost:8000/health
- فرانت‌اند: http://localhost:3000
- Grafana: http://localhost:3300 (کاربر/رمز پیش‌فرض dev: `admin`/`admin`)
- کنسول MinIO: http://localhost:9001

## تست

```bash
# بک‌اند
cd backend && pytest

# فرانت‌اند
cd frontend && npm run build && npm run lint
```

## ساختار پروژه

```
RoyaEvent/
  backend/    # FastAPI
  frontend/   # Next.js
  infra/      # docker-compose، Nginx، پیکربندی مانیتورینگ
  data/       # تحلیل رقبا
  docs/       # مستندات معماری
```
