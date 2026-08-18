from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class KpiDailySnapshot(Base, TimestampMixin):
    """رول‌آپ شبانه‌ی KPI (بخش ۳ و ۱۱ پلن معماری) — app/services/kpi_service.py
    این جدول رو از Mongo (رفتار خام) + کوئری‌های SQLite (مثل OTP) پر می‌کنه.
    dimensions_json برای معیارهایی مثل «کلیدواژه‌ی پرجستجو» که خودشون یک
    breakdown دارن (مثلاً {"keyword": "..."}) استفاده می‌شه؛ برای معیارهای
    ساده (مثل dau) همیشه "{}" است."""

    __tablename__ = "kpi_daily_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dimensions_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    value: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "snapshot_date", "metric_name", "dimensions_json", name="uq_kpi_daily_snapshot"
        ),
    )
