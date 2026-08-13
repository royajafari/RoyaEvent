# راهنمای دیپلوی production + TLS اجباری

بخشی از فاز ۱۱ (`docs/architecture.md` بخش ۱۴) که زودتر و مستقل انجام شد، چون کاربر صراحتاً روی الزامی‌بودن HTTPS تأکید کرد. این سند فقط پوشش‌دهنده‌ی **راه‌اندازی Nginx + Let's Encrypt** است؛ باقی فاز ۱۱ (استراتژی بکاپ، مدیریت secrets، مانیتورینگ production) بعداً و جدا مستند می‌شه.

## پیش‌نیازها

- یک VPS با Docker + Docker Compose نصب‌شده.
- یک دامنه که رکورد DNS نوع A ش به IP همون VPS اشاره کنه (مثلاً `royaevent.ir` → IP سرور). گواهی Let's Encrypt بدون این امکان‌پذیر نیست.
- پورت‌های ۸۰ و ۴۴۳ روی VPS باز باشن (فایروال/امنیت‌گروه).

## قدم ۱ — جایگزینی دامنه‌ی واقعی

همه‌جای `infra/nginx/conf.d/royaevent.conf` به‌جای `royaevent.example.com` دامنه‌ی واقعی‌تون رو بذارید:

```bash
sed -i 's/royaevent.example.com/دامنه‌ی-واقعی-شما/g' infra/nginx/conf.d/royaevent.conf
```

## قدم ۲ — env فایل‌ها

`backend/.env` رو با مقادیر واقعی production پر کنید (طبق `.env.example` ریشه‌ی ریپو) — حتماً `JWT_SECRET_KEY` و `OTP_HASH_SECRET` رو به مقادیر تصادفی امن تغییر بدید (پیش‌فرض‌های `CHANGE_ME_*` فقط برای dev هستن). برای object storage هم یکی از دو سناریو (ArvanCloud یا MinIO خودمیزبان از همین compose) رو در `MINIO_*` ست کنید.

کنار `infra/docker-compose.prod.yml` یک فایل `infra/.env` بسازید:

```env
DOMAIN_NAME=دامنه‌ی-واقعی-شما
MINIO_ROOT_USER=royaevent
MINIO_ROOT_PASSWORD=یک-پسورد-تصادفی-امن
```

## قدم ۳ — صدور اولیه‌ی گواهی (قبل از بالا آوردن nginx)

این مهم‌ترین نکته‌ست: **nginx بدون وجود فایل گواهی روی دیسک اصلاً بالا نمی‌آد** (چون `ssl_certificate` به فایلی اشاره می‌کنه که هنوز وجود نداره). پس گواهی باید قبل از استارت کل استک، با حالت مستقل (`--standalone`، وب‌سرور موقت خود certbot) صادر بشه — یعنی پورت ۸۰ باید در این لحظه آزاد باشه (nginx یا هر سرویس دیگه‌ای روش نباشه):

```bash
cd infra
docker compose -f docker-compose.prod.yml run --rm --service-ports \
  certbot certonly --standalone \
  -d دامنه‌ی-واقعی-شما \
  --email you@example.com --agree-tos --no-eff-email
```

(`--service-ports` لازمه چون در حالت عادی `docker compose run` پورت‌های تعریف‌شده‌ی سرویس رو منتشر نمی‌کنه؛ اینجا برای `--standalone` باید پورت ۸۰ واقعاً باز باشه. برای تمدید بعدی — قدم ۵ — دیگه نیازی به این فلگ نیست، چون روش webroot از volume مشترک استفاده می‌کنه، نه پورت مستقل.)

بعد از این دستور، گواهی زیر `certbot_conf` (volume مشترک با nginx) ذخیره می‌شه.

## قدم ۴ — بالا آوردن کل استک

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

حالا nginx با گواهی موجود بالا می‌آد، پورت ۸۰ همه‌چیز رو ریدایرکت به ۴۴۳ می‌کنه، و `https://دامنه‌ی-واقعی-شما` باید کار کنه.

## قدم ۵ — تمدید خودکار

Let's Encrypt هر ۹۰ روز منقضی می‌شه. چون کانتینر certbot به‌خاطر نداشتن دسترسی به docker socket نمی‌تونه مستقیم nginx رو reload کنه، تمدید از طریق یک اسکریپت روی **هاست** (نه داخل کانتینر) با کرون انجام می‌شه:

```bash
chmod +x infra/renew-certs.sh
crontab -e
# این خط رو اضافه کنید (هر روز ساعت ۳ بامداد):
0 3 * * * /مسیر/کامل/RoyaEvent/infra/renew-certs.sh >> /var/log/royaevent-renew.log 2>&1
```

اسکریپت هم `certbot renew` (که خودش no-op می‌مونه اگه هنوز زود باشه) و هم `nginx -s reload` رو پشت‌سرهم اجرا می‌کنه.

## نکات

- `frontend`/`backend` هیچ‌کدوم مستقیم پورت به بیرون expose نمی‌کنن — فقط nginx پشت TLS در دسترس عمومیه (`ports: 80/443` فقط روی سرویس nginx).
- `client_max_body_size 35M` در nginx برای عبور آپلود کلیپ تبلیغاتی (سقف ۳۰ مگابایت در بک‌اند) تنظیم شده — اگه سقف بک‌اند تغییر کرد، این‌جا هم باید هماهنگ بشه.
- برای SQLite/Chroma persistent بمونن، `SQLITE_PATH`/`CHROMA_PERSIST_DIR` در `backend/.env` باید به مسیر داخل volume mount شده اشاره کنن، مثلاً `SQLITE_PATH=/app/data/roya_event.db` (چون `backend_data` روی `/app/data` mount شده در `docker-compose.prod.yml`).
- استک monitoring (Loki/Prometheus/Grafana، فاز ۹) عمداً در این compose نیست — وقتی فاز ۹ شروع بشه جدا اضافه می‌شه.
