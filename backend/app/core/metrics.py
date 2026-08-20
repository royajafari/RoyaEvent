"""متریک‌های Prometheus (فاز ۹) — هم HTTP عمومی (توسط middleware در main.py پر
می‌شه) هم کسب‌وکاری (OTP/سفارش/صف اعلان، توسط سرویس‌های مربوطه).

نکته: notification_outbox_pending یه Gauge با set_function است، نه یه شمارنده
که جایی increment بشه — چون این عدد یه snapshot زنده از DB است، نه رویدادی که
لحظه‌ی رخ‌دادنش قابل شمارشه؛ محاسبه‌ش فقط موقع scrape شدن توسط Prometheus
اتفاق می‌افته (هزینه‌ی یک کوئری COUNT ساده، نه هر ثانیه)."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "royaevent_http_requests_total",
    "تعداد درخواست‌های HTTP",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "royaevent_http_request_duration_seconds",
    "تأخیر درخواست‌های HTTP (ثانیه)",
    ["method", "path"],
)

otp_requested_total = Counter(
    "royaevent_otp_requested_total",
    "تعداد درخواست‌های OTP ارسال‌شده",
    ["channel"],
)
otp_verified_total = Counter(
    "royaevent_otp_verified_total",
    "تعداد OTPهای با موفقیت تأییدشده",
    ["channel"],
)
otp_failed_total = Counter(
    "royaevent_otp_failed_total",
    "تعداد تلاش‌های ناموفق تأیید OTP (نامعتبر/منقضی/قفل‌شده)",
    ["channel"],
)

orders_completed_total = Counter(
    "royaevent_orders_completed_total",
    "تعداد سفارش‌های تکمیل‌شده (رایگان یا پولی)",
)

notification_outbox_pending = Gauge(
    "royaevent_notification_outbox_pending",
    "تعداد ردیف‌های در انتظار ارسال در صف اعلان (notification_outbox)",
)


def _pending_notification_count() -> float:
    # import محلی برای جلوگیری از circular import (metrics <- db.session <- ... )
    from app.db.session import SessionLocal
    from app.models.notification import NotificationOutbox, NotificationStatus

    # این callback بیرون از request scope (توسط collector خود Prometheus)
    # صدا زده می‌شه، پس نمی‌تونه از get_db تزریق‌شده استفاده کنه؛ مستقیم از
    # engine واقعی وصل می‌شه. اگه DB/جدول هنوز آماده نباشه (مثلاً محیط تست که
    # عمداً lifespan رو اجرا نمی‌کنه)، به‌جای crash کردن /metrics صفر برمی‌گردونه.
    try:
        db = SessionLocal()
        try:
            return float(
                db.query(NotificationOutbox)
                .filter(NotificationOutbox.status == NotificationStatus.PENDING)
                .count()
            )
        finally:
            db.close()
    except Exception:
        return 0.0


notification_outbox_pending.set_function(_pending_notification_count)
