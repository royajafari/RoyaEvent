# فاز ۱ — Auth/OTP + کاربران

وضعیت: ✅ کامل، تست‌شده، commit‌شده، push‌شده.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت backend/frontend + docker-compose سرویس‌های جانبی + مستندات پایه آماده‌ست. جزئیات: [`spec0.md`](spec0.md).

## هدف

احراز هویت OTP-only (بدون پسورد) طبق سند `docs/event_otp_email_sms_plan_fa.md` (منبع حقیقت پارامترهای OTP)، با JWT چرخشی (access کوتاه + refresh rotating).

## چیزی که ساخته شد

**بک‌اند:**
- جداول (Alembic): `users` (phone/email nullable+unique، full_name، role، status)، `otp_challenge` (طبق فیلدهای دقیق سند: destination, channel, purpose, otp_hash, attempt_count, max_attempts, status, ...)، `refresh_tokens` (token_hash, jti, expires_at, revoked_at, replaced_by — چرخش زنجیره‌ای).
- `app/services/otp_service.py` — تولید/هش/rate-limit/انقضا/قفل OTP.
- `app/services/auth_service.py` — صدور/چرخش JWT (access ۱۵ دقیقه، refresh ۳۰ روز rotating؛ استفاده‌ی مجدد از refresh باطل‌شده = تشخیص سرقت → کل خانواده‌ی توکن باطل می‌شه).
- Provider abstraction: `app/providers/sms/` (base + console/ippanel/kavenegar)، `app/providers/email/` (base + console/brevo/resend) — بدون API key در `.env`، خودکار می‌ره روی `ConsoleProvider` (فقط لاگ/حافظه، برای dev و تست).
- `app/core/rate_limit.py` — محدودیت اختصاصی OTP (جدا از میان‌افزار عمومی که در فاز ۲ اومد).
- `app/api/v1/routers/auth.py` — `POST /auth/otp/request`, `POST /auth/otp/resend`, `POST /auth/otp/verify` (برای purpose=LOGIN توکن هم صادر می‌کنه)، `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`.
- Refresh token در کوکی **httpOnly, Secure, SameSite=Lax**؛ access token فقط در پاسخ JSON (فرانت در حافظه نگه می‌داره، نه کوکی/localStorage) — محافظت در برابر XSS.

**فرانت‌اند:**
- `app/(auth)/login/page.tsx` — فرم دومرحله‌ای (مقصد → کد OTP)، تب پیامک/ایمیل، شمارش معکوس ارسال مجدد.
- `lib/api-client.ts` — fetch wrapper با `credentials:"include"` (برای کوکی refresh)، `authApi.*`.
- `store/auth-store.ts` — Zustand، access token فقط در حافظه.

**تست‌ها:** ۵۵ تست (unit + integration) — OTP request/verify/resend، rate-limit، چرخش JWT، تشخیص سرقت refresh. `tests/conftest.py` از `fakeredis` و یک SQLite موقت (`tmp_path`) استفاده می‌کنه — نیازی به Redis/DB واقعی نیست، CI بدون Docker هم پاس می‌شه.

## نکات/دام‌های این فاز

- endpoint دقیق IPPanel (`app/providers/sms/ippanel.py`) از مستندات رسمی تأیید **نشده** (سایتشون JS-render هست، WebFetch نتونست بخونه) — بر اساس الگوی متداول نوشته شده؛ قبل از استفاده‌ی واقعی با API key واقعی تست/تطبیق بده. Kavenegar و Brevo مستقیماً از داک رسمی تأیید شدن.
- برای دیدن OTP واقعی در تست، از پارس‌کردن لاگ استفاده نکن — `ConsoleSmsProvider`/`ConsoleEmailProvider` یک لیست `sent_messages` در حافظه دارن (`provider.sent_messages[-1]["message"]`)، پایدارتر از caplog.
- بدون `logging.basicConfig(...)` در `app/main.py`، لاگرهای خودمون (`ConsoleSmsProvider` و بقیه) در اجرای واقعی سرور (نه تست) اصلاً چاپ نمی‌شن — چون root logger پیش‌فرض Python سطح `WARNING` داره. این باعث شد اولین تلاش برای گرفتن OTP از لاگ سرور واقعی (تست دستی) هیچی نشون نده. فیکس یک‌بار در `app/main.py` انجام شد و برای همه‌ی فازهای بعد پابرجاست.

## راستی‌آزمایی

مسیر کامل ورود OTP لوکال کار کرد؛ چرخش refresh و محدودیت‌های OTP تست دارن (۵۵ تست پاس).

## Commitهای مرتبط

`c7f3274` (بک‌اند OTP/JWT)، `6de4f8e` (فرانت صفحه‌ی ورود)، `907facd` (docs)
