from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class PricingModel(str, enum.Enum):
    FREE = "free"
    PAID = "paid"
    DONATION = "donation"


class DiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class TicketType(Base, TimestampMixin):
    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # تومان، بدون اعشار
    pricing_model: Mapped[PricingModel] = mapped_column(Enum(PricingModel), nullable=False)
    quantity_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_early_bird: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class DiscountCode(Base, TimestampMixin):
    """کد تخفیف در سطح رویداد (توسط برگزارکننده)."""

    __tablename__ = "discount_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PlatformDiscountCode(Base, TimestampMixin):
    """کد تخفیف سراسری سایت (توسط ادمین) — طبق تصمیم کاربر، جدا از سطح رویداد."""

    __tablename__ = "platform_discount_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
