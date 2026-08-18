from datetime import date, datetime, timedelta

from app.models.kpi import KpiDailySnapshot
from app.models.otp_challenge import OTPChallenge, OTPChannel, OTPPurpose, OTPStatus
from app.services.kpi_service import get_kpi_report, rollup_daily_kpis

TARGET_DATE = date(2026, 6, 15)
MID_DAY = datetime(2026, 6, 15, 12, 0, 0)
OTHER_DAY = datetime(2026, 6, 14, 12, 0, 0)


def _metric(db_session, name: str, dimensions: str = "{}") -> KpiDailySnapshot | None:
    return (
        db_session.query(KpiDailySnapshot)
        .filter_by(snapshot_date=TARGET_DATE, metric_name=name, dimensions_json=dimensions)
        .first()
    )


def test_rollup_computes_funnel_counts_and_conversion(db_session, fake_mongo):
    steps = ["VIEW_EVENT", "VIEW_EVENT", "VIEW_EVENT", "CLICK_REGISTER", "START_CHECKOUT", "COMPLETE_ORDER"]
    for step in steps:
        fake_mongo["funnel_events"].insert_one({"session_id": "s1", "step": step, "ts": MID_DAY})
    # روز دیگه، نباید تو رول‌آپ این روز حساب بشه
    fake_mongo["funnel_events"].insert_one({"session_id": "s2", "step": "VIEW_EVENT", "ts": OTHER_DAY})

    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)

    assert _metric(db_session, "funnel_view_event").value == 3
    assert _metric(db_session, "funnel_click_register").value == 1
    assert _metric(db_session, "funnel_start_checkout").value == 1
    assert _metric(db_session, "funnel_complete_order").value == 1
    conversion = _metric(db_session, "funnel_conversion_view_to_complete_pct")
    assert round(conversion.value, 2) == round(1 / 3 * 100, 2)


def test_rollup_conversion_zero_when_no_views(db_session, fake_mongo):
    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)
    assert _metric(db_session, "funnel_conversion_view_to_complete_pct").value == 0.0


def test_rollup_computes_search_metrics_and_top_keywords(db_session, fake_mongo):
    fake_mongo["search_queries"].insert_many(
        [
            {"query_text": "پایتون", "result_count": 5, "ts": MID_DAY},
            {"query_text": "پایتون", "result_count": 5, "ts": MID_DAY},
            {"query_text": "جاوااسکریپت", "result_count": 2, "ts": MID_DAY},
            {"query_text": "چیز عجیب", "result_count": 0, "ts": MID_DAY},
        ]
    )

    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)

    assert _metric(db_session, "search_total_queries").value == 4
    assert _metric(db_session, "search_failed_queries").value == 1
    top_keyword = _metric(db_session, "search_keyword", dimensions='{"keyword": "پایتون"}')
    assert top_keyword is not None
    assert top_keyword.value == 2


def test_rollup_computes_dau_from_distinct_sessions(db_session, fake_mongo):
    fake_mongo["page_views"].insert_many(
        [
            {"session_id": "a", "path": "/", "ts": MID_DAY},
            {"session_id": "a", "path": "/events", "ts": MID_DAY},
            {"session_id": "b", "path": "/", "ts": MID_DAY},
        ]
    )

    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)

    assert _metric(db_session, "dau").value == 2


def test_rollup_computes_otp_health_from_sqlite(db_session, fake_mongo):
    def _make_otp(created_at: datetime, status: OTPStatus, used_at: datetime | None) -> OTPChallenge:
        return OTPChallenge(
            destination="09120000000",
            channel=OTPChannel.SMS,
            purpose=OTPPurpose.LOGIN,
            otp_hash="x",
            expires_at=created_at + timedelta(minutes=5),
            max_attempts=5,
            status=status,
            last_sent_at=created_at,
            created_at=created_at,
            used_at=used_at,
        )

    db_session.add_all(
        [
            _make_otp(MID_DAY, OTPStatus.VERIFIED, MID_DAY + timedelta(seconds=30)),
            _make_otp(MID_DAY, OTPStatus.EXPIRED, None),
            _make_otp(OTHER_DAY, OTPStatus.VERIFIED, OTHER_DAY + timedelta(seconds=30)),
        ]
    )
    db_session.commit()

    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)

    assert _metric(db_session, "otp_requested").value == 2
    assert _metric(db_session, "otp_verified").value == 1


def test_rollup_upserts_not_duplicates(db_session, fake_mongo):
    fake_mongo["page_views"].insert_one({"session_id": "a", "ts": MID_DAY})
    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)
    fake_mongo["page_views"].insert_one({"session_id": "b", "ts": MID_DAY})
    rollup_daily_kpis(db_session, fake_mongo, TARGET_DATE)

    rows = db_session.query(KpiDailySnapshot).filter_by(snapshot_date=TARGET_DATE, metric_name="dau").all()
    assert len(rows) == 1
    assert rows[0].value == 2


def test_get_kpi_report_filters_by_days(db_session, fake_mongo):
    old_date = date.today() - timedelta(days=30)
    recent_date = date.today() - timedelta(days=1)
    rollup_daily_kpis(db_session, fake_mongo, old_date)
    rollup_daily_kpis(db_session, fake_mongo, recent_date)

    report = get_kpi_report(db_session, days=7)
    dates = {row.snapshot_date for row in report}
    assert recent_date in dates
    assert old_date not in dates
