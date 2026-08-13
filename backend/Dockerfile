FROM python:3.12-slim AS base

WORKDIR /app

# بدون build-essential: تقریباً همه‌ی وابستگی‌ها (از جمله cryptography،
# Pillow، pymongo) برای linux/amd64 + py3.12 پکیج wheel آماده دارن، نیازی
# به کامپایل نیست. اگه یه پکیج جدید بدون wheel اضافه شد و pip install با
# خطای کامپایلر fail کرد، این لایه رو دوباره اضافه کن.
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=60 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8000

# قبل از بالا آمدن سرور، migration ها اجرا می‌شن — همیشه additive طبق قرارداد
# CLAUDE.md (هرگز جدول موجود drop نمی‌شه بدون بررسی دستی خروجی autogenerate)
CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --access-logfile - --error-logfile -"]
