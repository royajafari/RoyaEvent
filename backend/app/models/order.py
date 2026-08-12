from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    SIMULATED_PAID = "simulated_paid"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class RegistrationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)

    discount_code_id: Mapped[int | None] = mapped_column(ForeignKey("discount_codes.id"), nullable=True)
    platform_discount_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_discount_codes.id"), nullable=True
    )

    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.NOT_REQUIRED, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    ticket_type_id: Mapped[int] = mapped_column(ForeignKey("ticket_types.id"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("event_sessions.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)


class Registration(Base, TimestampMixin):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("event_sessions.id"), nullable=False, index=True)

    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus), default=RegistrationStatus.CONFIRMED, nullable=False
    )
    ticket_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)


class Payment(Base, TimestampMixin):
    """جدا از orders تا اتصال درگاه واقعی بعداً بدون تغییر مدل سفارش ممکن باشد."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="none", nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.NOT_REQUIRED, nullable=False
    )
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
