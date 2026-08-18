"""رول‌آپ شبانه‌ی KPI (بخش ۱۱ پلن معماری) — pipeline های Mongo (رفتار خام)
+ کوئری‌های SQLite (OTP) رو اجرا و در kpi_daily_snapshot ذخیره می‌کنه.
گزارش ادمین هم از همین جدول (نه مستقیم از Mongo) می‌خونه، تا خود endpoint
گزارش سبک/سریع بمونه و به سلامت Mongo در لحظه‌ی درخواست وابسته نباشه."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta

from pymongo.database import Database
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.kpi import KpiDailySnapshot
from app.models.otp_challenge import OTPChallenge, OTPStatus

_FUNNEL_STEPS = ["VIEW_EVENT", "CLICK_REGISTER", "START_CHECKOUT", "COMPLETE_ORDER"]


def _day_bounds(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, time.min)
    end = start + timedelta(days=1)
    return start, end


def _upsert_metric(
    db: Session, snapshot_date: date, metric_name: str, dimensions: dict, value: float
) -> None:
    dimensions_json = json.dumps(dimensions, ensure_ascii=False, sort_keys=True)
    row = (
        db.query(KpiDailySnapshot)
        .filter_by(snapshot_date=snapshot_date, metric_name=metric_name, dimensions_json=dimensions_json)
        .first()
    )
    if row is None:
        row = KpiDailySnapshot(
            snapshot_date=snapshot_date,
            metric_name=metric_name,
            dimensions_json=dimensions_json,
            value=value,
        )
        db.add(row)
    else:
        row.value = value


def rollup_daily_kpis(db: Session, mongo_db: Database, target_date: date) -> None:
    settings = get_settings()
    start, end = _day_bounds(target_date)
    ts_filter = {"ts": {"$gte": start, "$lt": end}}

    funnel_counts: dict[str, int] = {}
    for step in _FUNNEL_STEPS:
        count = mongo_db["funnel_events"].count_documents({**ts_filter, "step": step})
        funnel_counts[step] = count
        _upsert_metric(db, target_date, f"funnel_{step.lower()}", {}, count)

    view_count = funnel_counts["VIEW_EVENT"]
    complete_count = funnel_counts["COMPLETE_ORDER"]
    conversion_pct = (complete_count / view_count * 100) if view_count > 0 else 0.0
    _upsert_metric(db, target_date, "funnel_conversion_view_to_complete_pct", {}, conversion_pct)

    total_queries = mongo_db["search_queries"].count_documents(ts_filter)
    failed_queries = mongo_db["search_queries"].count_documents({**ts_filter, "result_count": 0})
    _upsert_metric(db, target_date, "search_total_queries", {}, total_queries)
    _upsert_metric(db, target_date, "search_failed_queries", {}, failed_queries)

    top_keywords = list(
        mongo_db["search_queries"].aggregate(
            [
                {"$match": ts_filter},
                {"$group": {"_id": "$query_text", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": settings.kpi_top_keywords_limit},
            ]
        )
    )
    for entry in top_keywords:
        keyword = entry.get("_id") or ""
        if not keyword:
            continue
        _upsert_metric(db, target_date, "search_keyword", {"keyword": keyword}, entry["count"])

    dau = len(mongo_db["page_views"].distinct("session_id", ts_filter))
    _upsert_metric(db, target_date, "dau", {}, dau)

    otp_requested = (
        db.query(OTPChallenge)
        .filter(OTPChallenge.created_at >= start, OTPChallenge.created_at < end)
        .count()
    )
    otp_verified = (
        db.query(OTPChallenge)
        .filter(
            OTPChallenge.status == OTPStatus.VERIFIED,
            OTPChallenge.used_at.isnot(None),
            OTPChallenge.used_at >= start,
            OTPChallenge.used_at < end,
        )
        .count()
    )
    _upsert_metric(db, target_date, "otp_requested", {}, otp_requested)
    _upsert_metric(db, target_date, "otp_verified", {}, otp_verified)

    db.commit()


def get_kpi_report(db: Session, days: int) -> list[KpiDailySnapshot]:
    since = date.today() - timedelta(days=days)
    return (
        db.query(KpiDailySnapshot)
        .filter(KpiDailySnapshot.snapshot_date >= since)
        .order_by(KpiDailySnapshot.snapshot_date.desc(), KpiDailySnapshot.metric_name)
        .all()
    )
