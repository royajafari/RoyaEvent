# Event Management — Email/SMS OTP Service Plan

> **نسخه:** 1.0  
> **تاریخ:** 1405/05/21 (2026-08-12)  
> **هدف:** طراحی و پیاده‌سازی سرویس OTP برای سامانه مدیریت ایونت با کمترین هزینه و قابلیت تعویض Provider.

---

## 1. تصمیم معماری

اصل مهم این پروژه:

**OTP داخل سامانه تولید و مدیریت می‌شود؛ Provider فقط کانال ارسال است.**

```text
User
  |
  | درخواست OTP
  v
Event Management API
  |
  v
OTP Service
  |-- Generate OTP
  |-- Hash OTP
  |-- Expiration
  |-- Attempt Limit
  |-- Rate Limit
  |-- Audit
  |
  +--------------------+
  |                    |
  v                    v
SMS Provider        Email Provider
(IPPanel /          Brevo
 Kavenegar)         یا Resend)
  |                    |
  v                    v
 Mobile              Email
```

مزیت: در آینده می‌توان SMS یا Email Provider را بدون تغییر منطق OTP عوض کرد.

---

# 2. Providerهای پیشنهادی

## 2.1 Email — انتخاب اول: Brevo

Brevo در پلن Free فعلی، 300 ارسال Email در روز دارد و این پلن محدودیت زمانی ندارد. همچنین Transactional Email در پلن Free ارائه می‌شود.

منبع رسمی:
https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans

محدودیت Free:
- 300 Email در روز
- تا 100,000 Contact
- Transactional Email
- API
- بدون محدودیت زمانی برای Free
- ایمیل‌های ارسال‌شده از Free شامل برندینگ Brevo هستند.

منبع:
https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan

### راه‌اندازی

1. ایجاد حساب Brevo.
2. ایجاد Sender.
3. ترجیحاً احراز Domain.
4. ایجاد API Key.
5. نگهداری API Key در Environment Variable.
6. پیاده‌سازی EmailProvider در سامانه.

نمونه تنظیمات:

```env
EMAIL_PROVIDER=brevo
BREVO_API_KEY=***
BREVO_SENDER_EMAIL=no-reply@example.com
BREVO_SENDER_NAME=Event Management
```

### گزینه جایگزین Email: Resend

Resend در Free فعلی:
- 3,000 Email در ماه
- حداکثر 100 Email در روز
- یک Domain
- REST API
- 30 روز Data Retention

منبع رسمی:
https://resend.com/pricing

برای شروع پروژه، Brevo به دلیل سقف روزانه بالاتر انتخاب اول است.

---

# 3. SMS — انتخاب اول برای تست: IPPanel

برای SMS ایرانی، IPPanel و Kavenegar را به‌عنوان دو Provider اصلی در معماری نگه می‌داریم.

### اولویت پیشنهادی

1. IPPanel — Provider اولیه
2. Kavenegar — Provider جایگزین

نکته مهم:

**رایگان بودن SMS را به‌عنوان یک قابلیت دائمی فرض نکنید.**

اگر Provider اعتبار تست یا پیامک آزمایشی ارائه کرد، از آن برای Development استفاده کنید؛ برای Production باید هزینه واقعی ارسال، خط خدماتی و شرایط ارسال OTP بررسی شود.

---

# 4. طراحی OTP

## 4.1 مشخصات پیشنهادی

| پارامتر | مقدار پیشنهادی |
|---|---:|
| طول OTP | 6 رقم |
| اعتبار | 5 دقیقه |
| حداکثر تلاش | 5 |
| فاصله درخواست مجدد | 60 ثانیه |
| حداکثر OTP در 1 ساعت برای شماره | 5 |
| حداکثر OTP در 24 ساعت برای شماره | 20 |
| OTP یک‌بارمصرف | بله |
| ذخیره OTP خام | خیر |
| ذخیره Hash | بله |

این مقادیر در Development قابل تغییر باشند.

---

# 5. تولید OTP

OTP باید با Random امن تولید شود.

نمونه منطقی:

```text
otp = SecureRandom(000000 .. 999999)
```

از Random معمولی زبان برنامه‌نویسی برای OTP استفاده نشود.

مثلاً:

```text
OTP = 583921
```

---

# 6. ذخیره‌سازی امن OTP

OTP خام نباید در Database ذخیره شود.

به‌جای:

```text
otp = 583921
```

از Hash استفاده شود:

```text
otp_hash = HMAC-SHA256(secret, otp + challenge_id)
```

در Database موارد زیر ذخیره شوند:

```text
otp_challenge
-------------------------
id
user_id / registration_id
destination
channel
otp_hash
created_at
expires_at
attempt_count
max_attempts
used_at
status
request_ip
provider_message_id
last_sent_at
```

### نکته

`destination` می‌تواند شماره موبایل یا Email باشد.

---

# 7. Expiration

OTP باید زمان انقضا داشته باشد.

پیشنهاد:

```text
created_at = 10:00:00
expires_at = 10:05:00
```

در زمان Verify:

```text
if now > expires_at:
    reject("OTP expired")
```

پس از Verify موفق:

```text
status = VERIFIED
used_at = now
```

و همان OTP دیگر قابل استفاده نباشد.

---

# 8. Rate Limit

Rate Limit باید حداقل در سه سطح اعمال شود.

## 8.1 سطح شماره/Email

مثلاً:

```text
1 OTP / 60 seconds
5 OTP / hour
20 OTP / day
```

هدف: جلوگیری از SMS/Email Spam.

---

## 8.2 سطح IP

مثلاً:

```text
10 OTP requests / 10 minutes / IP
```

هدف: جلوگیری از حمله از یک IP.

---

## 8.3 سطح کاربر

اگر User Account وجود دارد:

```text
5 OTP requests / hour / user
```

---

# 9. Attempt Limit

Rate Limit با Attempt Limit فرق دارد.

مثلاً کاربر OTP دریافت کرده است.

حداکثر:

```text
5 attempts
```

بعد از پنجمین خطای متوالی:

```text
status = LOCKED
```

و کاربر باید OTP جدید درخواست کند.

---

# 10. API طراحی پیشنهادی

## Request OTP

```http
POST /api/v1/auth/otp/request
Content-Type: application/json
```

```json
{
  "channel": "sms",
  "destination": "09121234567",
  "purpose": "event_registration"
}
```

Response:

```json
{
  "success": true,
  "challenge_id": "01J...",
  "expires_in": 300,
  "retry_after": 60
}
```

**OTP هرگز در Response برگردانده نشود.**

---

# 11. Verify OTP

```http
POST /api/v1/auth/otp/verify
Content-Type: application/json
```

```json
{
  "challenge_id": "01J...",
  "otp": "583921"
}
```

Response موفق:

```json
{
  "success": true,
  "verified": true
}
```

Response ناموفق:

```json
{
  "success": false,
  "verified": false,
  "message": "Invalid or expired OTP"
}
```

برای جلوگیری از User Enumeration بهتر است خطاهای OTP بیش از حد جزئی نباشند.

---

# 12. جریان کامل SMS OTP

```text
1. User enters mobile
        |
2. POST /otp/request
        |
3. Check Rate Limit
        |
4. Generate 6-digit OTP
        |
5. Hash OTP
        |
6. Save challenge
        |
7. Send SMS through Provider
        |
8. Return challenge_id
        |
9. User enters OTP
        |
10. POST /otp/verify
        |
11. Check expiration
        |
12. Check attempts
        |
13. Hash submitted OTP
        |
14. Compare hashes
        |
15. Mark challenge as VERIFIED
```

---

# 13. جریان Email OTP

دقیقاً همان جریان SMS است.

فقط Channel تغییر می‌کند:

```text
channel = email
```

و Provider:

```text
Brevo
```

Subject پیشنهادی:

```text
کد تأیید ثبت‌نام در رویداد
```

محتوای Email:

```text
کد تأیید شما:

583921

این کد تا 5 دقیقه معتبر است.

اگر این درخواست توسط شما انجام نشده است، این پیام را نادیده بگیرید.
```

---

# 14. Provider Abstraction

در Backend یک Interface تعریف شود:

```text
NotificationProvider
```

و پیاده‌سازی‌ها:

```text
SmsProvider
 ├── IPPanelProvider
 └── KavenegarProvider

EmailProvider
 ├── BrevoProvider
 └── ResendProvider
```

Business Logic نباید مستقیماً Kavenegar یا IPPanel را صدا بزند.

مثلاً:

```text
OTPService
    |
    +--> SmsProvider.send(...)
```

نه:

```text
OTPService
    |
    +--> Kavenegar.send(...)
```

---

# 15. Database پیشنهادی

حداقل یک جدول:

```sql
OTP_CHALLENGE
```

فیلدهای پیشنهادی:

```text
ID
USER_ID
EVENT_ID
DESTINATION
CHANNEL
PURPOSE
OTP_HASH
CREATED_AT
EXPIRES_AT
ATTEMPT_COUNT
MAX_ATTEMPTS
STATUS
USED_AT
LAST_SENT_AT
REQUEST_IP
PROVIDER
PROVIDER_MESSAGE_ID
CREATED_BY
```

Status:

```text
PENDING
VERIFIED
EXPIRED
LOCKED
CANCELLED
```

---

# 16. Security Rules

حتماً این موارد رعایت شوند:

- OTP خام در DB ذخیره نشود.
- OTP در Log ثبت نشود.
- OTP در Response API برگردانده نشود.
- API Key Provider داخل Source Code نباشد.
- API Key در Environment Variable یا Secret Manager باشد.
- HTTPS اجباری باشد.
- Rate Limit سمت Server اعمال شود.
- تعداد Attempt محدود باشد.
- OTP بعد از موفقیت Immediately مصرف شود.
- OTP منقضی‌شده قابل استفاده نباشد.
- درخواست‌های OTP Audit شوند.
- IP و User-Agent در صورت نیاز برای امنیت ثبت شوند.
- Error Message اطلاعات اضافه درباره وجود/عدم وجود User ندهد.

---

# 17. جلوگیری از SMS Bombing

یک نکته بسیار مهم برای سامانه Event:

کاربر نباید بتواند مرتب روی:

```text
ارسال مجدد کد
```

کلیک کند.

پیشنهاد UI:

```text
ارسال مجدد کد
[ 58 ثانیه ]
```

بعد از پایان Countdown:

```text
ارسال مجدد کد
```

اما حتی اگر کاربر API را مستقیماً صدا بزند، Server باید Rate Limit را اعمال کند.

---

# 18. Failover

در مرحله اول لازم نیست Failover واقعی پیاده شود.

ولی Interface باید طوری باشد که بعداً بتوانیم اضافه کنیم:

```text
OTPService
    |
    v
SmsProviderManager
    |
    +--> IPPanel
    |
    +--> Kavenegar
```

در صورت Fail شدن Provider اصلی:

```text
IPPanel failed
       |
       v
Kavenegar
```

البته Failover باید با احتیاط انجام شود تا یک OTP دوبار ارسال نشود.

---

# 19. برنامه اجرای پروژه

## Phase 1 — زیرساخت

- [ ] ایجاد حساب Brevo
- [ ] ایجاد Sender
- [ ] ایجاد API Key
- [ ] ثبت Domain در صورت امکان
- [ ] ایجاد حساب IPPanel
- [ ] دریافت API Credential
- [ ] بررسی اعتبار تست/هدیه SMS
- [ ] بررسی Pattern/OTP
- [ ] ایجاد Environment Variables

## Phase 2 — OTP Core

- [ ] ایجاد جدول OTP_CHALLENGE
- [ ] پیاده‌سازی Secure OTP Generator
- [ ] پیاده‌سازی Hash
- [ ] پیاده‌سازی Expiration
- [ ] پیاده‌سازی Attempt Limit
- [ ] پیاده‌سازی Rate Limit
- [ ] پیاده‌سازی Audit

## Phase 3 — Notification

- [ ] ایجاد SmsProvider Interface
- [ ] پیاده‌سازی IPPanelProvider
- [ ] ایجاد KavenegarProvider به‌صورت آماده برای جایگزینی
- [ ] ایجاد EmailProvider Interface
- [ ] پیاده‌سازی BrevoProvider
- [ ] آماده‌سازی ResendProvider

## Phase 4 — API

- [ ] POST /otp/request
- [ ] POST /otp/verify
- [ ] POST /otp/resend
- [ ] مدیریت Errorها
- [ ] Rate Limit Middleware
- [ ] Audit Log

## Phase 5 — UI

- [ ] ورود شماره موبایل/Email
- [ ] نمایش Countdown
- [ ] ورود OTP
- [ ] نمایش تعداد تلاش باقی‌مانده
- [ ] Resend
- [ ] پیام موفقیت/خطا

## Phase 6 — تست

- [ ] OTP صحیح
- [ ] OTP غلط
- [ ] OTP منقضی‌شده
- [ ] OTP دوبار مصرف‌شده
- [ ] 5 تلاش ناموفق
- [ ] Rate Limit
- [ ] IP Rate Limit
- [ ] SMS Provider failure
- [ ] Email Provider failure
- [ ] Duplicate request
- [ ] Concurrent requests

---

# 20. تنظیمات پیشنهادی اولیه

```env
OTP_LENGTH=6
OTP_EXPIRATION_SECONDS=300

OTP_MAX_ATTEMPTS=5

OTP_RESEND_COOLDOWN_SECONDS=60

OTP_MAX_REQUESTS_PER_MINUTE=1
OTP_MAX_REQUESTS_PER_HOUR=5
OTP_MAX_REQUESTS_PER_DAY=20

OTP_IP_MAX_REQUESTS_PER_10_MINUTES=10

SMS_PROVIDER=ippanel
EMAIL_PROVIDER=brevo
```

مقادیر Rate Limit باید بعد از تست واقعی سامانه تنظیم شوند.

---

# 21. انتخاب نهایی برای MVP

### Email

**Brevo**

```text
Free
300 emails/day
Transactional Email
API
```

### SMS

**IPPanel**

```text
Provider اصلی MVP
Pattern/OTP
API
ایرانی
```

### Backup

```text
Kavenegar
```

### OTP

```text
خود سامانه
6 digit
5 min expiration
5 attempts
60 sec resend cooldown
Rate limiting
Hash storage
One-time use
```

---

# 22. نکته مهم درباره «رایگان»

Email واقعاً می‌تواند برای MVP رایگان باشد؛ Brevo Free فعلاً 300 ارسال در روز دارد.

اما برای SMS ایرانی، «رایگان دائمی» را نباید جزء فرضیات معماری قرار داد. بهترین استراتژی این است که Provider API را Abstract کنیم و در Development از اعتبار تست/رایگان احتمالی استفاده کنیم. برای Production، هزینه پیامک را در برآورد پروژه لحاظ کنیم.

---

# 23. منابع رسمی

- Brevo Pricing:
  https://www.brevo.com/pricing/

- Brevo Free Plan:
  https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan

- Brevo API Rate Limits:
  https://developers.brevo.com/docs/api-limits

- Resend Pricing:
  https://resend.com/pricing

- IPPanel API Documentation:
  https://apidoc.ippanel.com/

- Kavenegar:
  https://kavenegar.com/
