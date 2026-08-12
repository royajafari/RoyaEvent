from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.slug import generate_alnum_code
from app.models.base import utcnow
from app.models.event import Event, EventSession, EventStatus
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus, Registration, RegistrationStatus
from app.models.ticket import DiscountCode, PlatformDiscountCode, PricingModel, TicketType
from app.schemas.order import OrderCreateIn
from app.services.discount_service import compute_discount_amount, find_valid_discount
from app.services.ticket_service import is_early_bird_active


class OrderServiceError(ValueError):
    pass


def _confirmed_registration_count(db: Session, session_id: int) -> int:
    return (
        db.query(Registration)
        .filter_by(session_id=session_id, status=RegistrationStatus.CONFIRMED)
        .count()
    )


def create_order(db: Session, user_id: int, data: OrderCreateIn) -> Order:
    ticket_type = db.get(TicketType, data.ticket_type_id)
    if ticket_type is None:
        raise OrderServiceError("نوع بلیط یافت نشد")

    session = db.get(EventSession, data.session_id)
    if session is None or session.event_id != ticket_type.event_id:
        raise OrderServiceError("جلسه‌ی انتخاب‌شده برای این رویداد معتبر نیست")

    event = db.get(Event, ticket_type.event_id)
    if event is None or event.status != EventStatus.PUBLISHED:
        raise OrderServiceError("این رویداد در حال حاضر قابل ثبت‌نام نیست")

    if ticket_type.is_early_bird and not is_early_bird_active(event):
        raise OrderServiceError("مهلت بلیط زودهنگام به پایان رسیده است")

    if ticket_type.quantity_total is not None and ticket_type.quantity_sold >= ticket_type.quantity_total:
        raise OrderServiceError("ظرفیت این نوع بلیط تکمیل شده است")

    if session.capacity is not None and _confirmed_registration_count(db, session.id) >= session.capacity:
        raise OrderServiceError("ظرفیت این جلسه تکمیل شده است")

    subtotal = ticket_type.price
    discount_amount = 0
    discount_code_id = None
    platform_discount_code_id = None

    if data.discount_code:
        record = find_valid_discount(db, event.id, data.discount_code)
        if record is None:
            raise OrderServiceError("کد تخفیف نامعتبر یا منقضی‌شده است")
        discount_amount = compute_discount_amount(subtotal, record)
        if isinstance(record, DiscountCode):
            discount_code_id = record.id
        elif isinstance(record, PlatformDiscountCode):
            platform_discount_code_id = record.id

    total = subtotal - discount_amount
    is_free = ticket_type.pricing_model == PricingModel.FREE
    payment_status = PaymentStatus.NOT_REQUIRED if is_free else PaymentStatus.PENDING

    order = Order(
        user_id=user_id,
        event_id=event.id,
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total=total,
        discount_code_id=discount_code_id,
        platform_discount_code_id=platform_discount_code_id,
        payment_status=payment_status,
    )
    db.add(order)
    db.flush()

    order_item = OrderItem(
        order_id=order.id,
        ticket_type_id=ticket_type.id,
        session_id=session.id,
        quantity=1,
        unit_price=subtotal,
        line_total=total,
    )
    db.add(order_item)
    db.commit()
    db.refresh(order)
    return order


def complete_order(db: Session, order: Order) -> Order:
    if order.status != OrderStatus.PENDING:
        raise OrderServiceError("این سفارش قابل تکمیل نیست")

    order_item = db.query(OrderItem).filter_by(order_id=order.id).first()
    ticket_type = db.get(TicketType, order_item.ticket_type_id)

    # بازبینی ظرفیت لحظه‌ی تکمیل (best-effort؛ قفل واقعی همزمانی در آینده)
    if ticket_type.quantity_total is not None and ticket_type.quantity_sold >= ticket_type.quantity_total:
        raise OrderServiceError("ظرفیت این نوع بلیط تکمیل شده است")

    ticket_type.quantity_sold += 1

    if order.payment_status == PaymentStatus.PENDING:
        order.payment_status = PaymentStatus.SIMULATED_PAID

    order.status = OrderStatus.COMPLETED
    order.completed_at = utcnow()

    if order.discount_code_id is not None:
        code = db.get(DiscountCode, order.discount_code_id)
        code.uses_count += 1
    if order.platform_discount_code_id is not None:
        platform_code = db.get(PlatformDiscountCode, order.platform_discount_code_id)
        platform_code.uses_count += 1

    registration = Registration(
        order_item_id=order_item.id,
        user_id=order.user_id,
        event_id=order.event_id,
        session_id=order_item.session_id,
        status=RegistrationStatus.CONFIRMED,
        ticket_code=generate_alnum_code(10),
    )
    db.add(registration)
    db.commit()
    db.refresh(order)
    return order


def cancel_registration(db: Session, registration: Registration) -> Registration:
    if registration.status != RegistrationStatus.CONFIRMED:
        raise OrderServiceError("این ثبت‌نام قبلاً لغو شده است")

    registration.status = RegistrationStatus.CANCELLED

    order_item = db.get(OrderItem, registration.order_item_id)
    ticket_type = db.get(TicketType, order_item.ticket_type_id)
    ticket_type.quantity_sold = max(0, ticket_type.quantity_sold - 1)

    db.commit()
    db.refresh(registration)
    return registration
