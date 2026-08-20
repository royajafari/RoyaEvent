"""پردازه‌ی جدا، خارج از worker‌های Gunicorn/uvicorn (بخش ۱ پلن معماری).

اجرا: python -m app.workers.scheduler

دو job دوره‌ای:
  - dispatch_outbox: صف notification_outbox رو می‌خونه و واقعاً از طریق
    SmsProvider/EmailProvider ارسال می‌کنه (هر ۱۵ ثانیه، پیش‌فرض).
  - scan_reminders: registrationهایی که جلسه‌شون ۵۹-۶۱ دقیقه‌ی دیگه شروع
    می‌شه و هنوز یادآوری نگرفتن رو صف می‌کنه (هر ۶۰ ثانیه، پیش‌فرض).

صحت هر دو job از طریق وضعیت دیتابیس تضمین می‌شه (status=PENDING،
reminder_sent_at IS NULL) نه وضعیت خود APScheduler — پس این پردازه هر وقت
crash/restart کنه، کاری duplicate/missed نمی‌شه. قفل Redis (SET NX EX)
هم محافظت اضافه‌ست برای وقتی این worker بعداً replica بشه.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import setup_json_logging
from app.core.mongo_client import get_mongo_db
from app.core.redis_client import get_redis
from app.db.session import SessionLocal
from app.models.base import utcnow
from app.models.event import Event, EventSession, EventStatus
from app.models.notification import NotificationChannel, NotificationOutbox, NotificationStatus
from app.models.order import Registration, RegistrationStatus
from app.models.user import User
from app.providers.email.factory import get_email_provider
from app.providers.sms.factory import get_sms_provider
from app.services import kpi_service, notification_service
from app.services.notification_templates import render_email, render_sms

logger = logging.getLogger(__name__)
settings = get_settings()

_DISPATCH_LOCK_KEY = "lock:notification-dispatch"
_REMINDER_LOCK_KEY = "lock:reminder-scan"
_KPI_ROLLUP_LOCK_KEY = "lock:kpi-rollup"
_BATCH_SIZE = 50


def _with_lock(key: str, ttl_seconds: int, fn) -> None:
    redis_client = get_redis()
    if not redis_client.set(key, "1", nx=True, ex=ttl_seconds):
        return
    try:
        fn()
    finally:
        redis_client.delete(key)


def _mark_retry_or_failed(row: NotificationOutbox, error: str) -> None:
    row.last_error = error[:2000]
    if row.attempts >= settings.notification_max_attempts:
        row.status = NotificationStatus.FAILED
    else:
        backoff_seconds = min(30 * (2 ** (row.attempts - 1)), 3600)
        row.next_attempt_at = utcnow() + timedelta(seconds=backoff_seconds)


def _send_one(row: NotificationOutbox) -> None:
    payload = json.loads(row.payload_json)
    row.attempts += 1
    try:
        if row.channel == NotificationChannel.SMS:
            text = render_sms(row.template_key, payload)
            result = get_sms_provider().send(row.destination, text)
        else:
            subject, body = render_email(row.template_key, payload)
            result = get_email_provider().send(row.destination, subject, body)

        if result.success:
            row.status = NotificationStatus.SENT
            row.provider = result.provider
            row.provider_message_id = result.provider_message_id
        else:
            _mark_retry_or_failed(row, "provider گزارش شکست ارسال داد")
    except Exception as exc:
        logger.warning("send failed for notification_outbox %s", row.id, exc_info=True)
        _mark_retry_or_failed(row, str(exc))


def dispatch_outbox(db: Session | None = None) -> None:
    """db اختیاریه تا تست‌ها بتونن session ایزوله‌ی خودشون رو تزریق کنن؛
    در اجرای واقعی (APScheduler) بدون آرگومان صدا زده می‌شه و خودش یه
    session جدا از SessionLocal واقعی می‌سازه/می‌بنده."""
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    try:
        now = utcnow()
        rows = (
            db.query(NotificationOutbox)
            .filter(
                NotificationOutbox.status == NotificationStatus.PENDING,
                NotificationOutbox.next_attempt_at <= now,
            )
            .limit(_BATCH_SIZE)
            .all()
        )
        for row in rows:
            _send_one(row)
            db.commit()
    finally:
        if owns_session:
            db.close()


def scan_reminders(db: Session | None = None) -> None:
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    try:
        now = utcnow()
        window_start = now + timedelta(minutes=59)
        window_end = now + timedelta(minutes=61)
        due = (
            db.query(Registration)
            .join(EventSession, EventSession.id == Registration.session_id)
            .join(Event, Event.id == Registration.event_id)
            .filter(
                Registration.status == RegistrationStatus.CONFIRMED,
                Registration.reminder_sent_at.is_(None),
                Event.status == EventStatus.PUBLISHED,
                EventSession.starts_at >= window_start,
                EventSession.starts_at <= window_end,
            )
            .all()
        )
        for registration in due:
            event = db.get(Event, registration.event_id)
            session = db.get(EventSession, registration.session_id)
            user = db.get(User, registration.user_id)
            notification_service.notify_event_reminder(db, user=user, event=event, session=session)
            registration.reminder_sent_at = now
            db.commit()
    finally:
        if owns_session:
            db.close()


def rollup_kpis(db: Session | None = None, target_date: date | None = None) -> None:
    """دیروز (به‌وقت UTC) رو رول‌آپ می‌کنه — چون رفتار امروز هنوز کامل نشده.
    مثل bقیه‌ی jobها db اختیاریه (تست session ایزوله تزریق می‌کنه)."""
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    try:
        day = target_date if target_date is not None else (utcnow().date() - timedelta(days=1))
        kpi_service.rollup_daily_kpis(db, get_mongo_db(), day)
    finally:
        if owns_session:
            db.close()


def run() -> None:
    setup_json_logging(level=logging.INFO, file_path=settings.log_file_path)
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        lambda: _with_lock(_DISPATCH_LOCK_KEY, 60, dispatch_outbox),
        "interval",
        seconds=settings.notification_dispatch_interval_seconds,
        id="dispatch_outbox",
        max_instances=1,
    )
    scheduler.add_job(
        lambda: _with_lock(_REMINDER_LOCK_KEY, 300, scan_reminders),
        "interval",
        seconds=settings.reminder_scan_interval_seconds,
        id="scan_reminders",
        max_instances=1,
    )
    scheduler.add_job(
        lambda: _with_lock(_KPI_ROLLUP_LOCK_KEY, 3600, rollup_kpis),
        "cron",
        hour=settings.kpi_rollup_hour_utc,
        minute=settings.kpi_rollup_minute_utc,
        id="rollup_kpis",
        max_instances=1,
    )
    logger.info("RoyaEvent notification worker started")
    scheduler.start()


if __name__ == "__main__":
    run()
