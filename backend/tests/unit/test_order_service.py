from datetime import timedelta

import pytest

from app.models.base import utcnow
from app.models.order import OrderStatus, PaymentStatus, RegistrationStatus
from app.models.ticket import DiscountCode, DiscountType
from app.schemas.order import OrderCreateIn
from app.schemas.ticket import TicketTypeIn
from app.services import ticket_service
from app.services.order_service import (
    OrderServiceError,
    cancel_registration,
    check_in_registration,
    complete_order,
    create_order,
)


def _order_in(ticket_type, session, discount_code=None) -> OrderCreateIn:
    return OrderCreateIn(
        ticket_type_id=ticket_type.id, session_id=session.id, discount_code=discount_code
    )


def test_create_order_free_ticket(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))

    assert order.status == OrderStatus.PENDING
    assert order.subtotal == 0
    assert order.total == 0
    assert order.payment_status == PaymentStatus.NOT_REQUIRED


def test_create_order_paid_ticket(db_session, published_event, buyer, paid_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(paid_ticket_type, session))

    assert order.subtotal == 150000
    assert order.total == 150000
    assert order.payment_status == PaymentStatus.PENDING


def test_create_order_with_valid_discount(db_session, published_event, buyer, paid_ticket_type):
    code = DiscountCode(
        event_id=published_event.id, code="OFF10", discount_type=DiscountType.PERCENT, value=10
    )
    db_session.add(code)
    db_session.commit()

    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(paid_ticket_type, session, "OFF10"))

    assert order.discount_amount == 15000
    assert order.total == 135000
    assert order.discount_code_id == code.id


def test_create_order_with_invalid_discount_raises(db_session, published_event, buyer, paid_ticket_type):
    session = published_event.sessions[0]
    with pytest.raises(OrderServiceError):
        create_order(db_session, buyer.id, _order_in(paid_ticket_type, session, "NOT_REAL"))


def test_create_order_unknown_ticket_type_raises(db_session, published_event, buyer):
    session = published_event.sessions[0]
    bad_order = OrderCreateIn(ticket_type_id=999999, session_id=session.id)
    with pytest.raises(OrderServiceError):
        create_order(db_session, buyer.id, bad_order)


def test_create_order_session_from_other_event_raises(
    db_session, published_event, buyer, free_ticket_type, leaf_category, organizer
):
    from datetime import datetime

    from app.schemas.event import EventCreateIn, EventSessionIn
    from app.services import event_service

    other_event = event_service.create_event(
        db_session,
        organizer.id,
        EventCreateIn(
            title="رویداد دیگر",
            description="توضیحات",
            category_id=leaf_category.id,
            format="online",
            online_platform_name="SkyRoom",
            sessions=[EventSessionIn(starts_at=datetime.now() + timedelta(days=3), duration_minutes=30)],
        ),
    )
    other_session = other_event.sessions[0]

    with pytest.raises(OrderServiceError):
        create_order(db_session, buyer.id, _order_in(free_ticket_type, other_session))


def test_create_order_for_unpublished_event_raises(
    db_session, leaf_category, organizer, buyer
):
    from datetime import datetime

    from app.schemas.event import EventCreateIn, EventSessionIn
    from app.services import event_service

    draft_event = event_service.create_event(
        db_session,
        organizer.id,
        EventCreateIn(
            title="پیش‌نویس",
            description="توضیحات",
            category_id=leaf_category.id,
            format="online",
            online_platform_name="SkyRoom",
            sessions=[EventSessionIn(starts_at=datetime.now() + timedelta(days=3), duration_minutes=30)],
        ),
    )
    ticket_type = ticket_service.create_ticket_type(
        db_session, draft_event, TicketTypeIn(name="بلیط", pricing_model="free")
    )

    with pytest.raises(OrderServiceError):
        create_order(db_session, buyer.id, _order_in(ticket_type, draft_event.sessions[0]))


def test_create_order_sold_out_ticket_type_raises(db_session, published_event, buyer):
    limited = ticket_service.create_ticket_type(
        db_session, published_event, TicketTypeIn(name="محدود", pricing_model="free", quantity_total=1)
    )
    limited.quantity_sold = 1
    db_session.commit()

    with pytest.raises(OrderServiceError):
        create_order(db_session, buyer.id, _order_in(limited, published_event.sessions[0]))


def test_create_order_session_capacity_full_raises(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    session.capacity = 1
    db_session.commit()

    first_order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, first_order)

    from app.models.user import User

    second_buyer = User(phone="09371234567")
    db_session.add(second_buyer)
    db_session.commit()
    db_session.refresh(second_buyer)

    with pytest.raises(OrderServiceError):
        create_order(db_session, second_buyer.id, _order_in(free_ticket_type, session))


def test_create_order_early_bird_rejected_after_window(db_session, published_event, buyer):
    session = published_event.sessions[0]
    published_event.published_at = utcnow() - timedelta(days=8)
    db_session.commit()

    early_bird = ticket_service.create_ticket_type(
        db_session, published_event, TicketTypeIn(name="زودهنگام", pricing_model="free", is_early_bird=True)
    )

    with pytest.raises(OrderServiceError):
        create_order(db_session, buyer.id, _order_in(early_bird, session))


def test_complete_order_free_creates_registration(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    completed = complete_order(db_session, order)

    assert completed.status == OrderStatus.COMPLETED
    assert completed.payment_status == PaymentStatus.NOT_REQUIRED
    assert completed.completed_at is not None

    from app.models.order import Registration

    registrations = db_session.query(Registration).filter_by(user_id=buyer.id).all()
    assert len(registrations) == 1
    assert registrations[0].status == RegistrationStatus.CONFIRMED
    assert len(registrations[0].ticket_code) == 10


def test_complete_order_paid_marks_simulated_paid(db_session, published_event, buyer, paid_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(paid_ticket_type, session))
    completed = complete_order(db_session, order)
    assert completed.payment_status == PaymentStatus.SIMULATED_PAID


def test_complete_order_increments_ticket_quantity_sold(
    db_session, published_event, buyer, free_ticket_type
):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)
    db_session.refresh(free_ticket_type)
    assert free_ticket_type.quantity_sold == 1


def test_complete_order_increments_discount_uses_count(db_session, published_event, buyer, paid_ticket_type):
    code = DiscountCode(
        event_id=published_event.id, code="ONCE", discount_type=DiscountType.FIXED, value=1000
    )
    db_session.add(code)
    db_session.commit()

    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(paid_ticket_type, session, "ONCE"))
    complete_order(db_session, order)
    db_session.refresh(code)
    assert code.uses_count == 1


def test_complete_order_twice_raises(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)

    with pytest.raises(OrderServiceError):
        complete_order(db_session, order)


def test_cancel_registration_frees_capacity(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)
    db_session.refresh(free_ticket_type)
    assert free_ticket_type.quantity_sold == 1

    from app.models.order import Registration

    registration = db_session.query(Registration).filter_by(user_id=buyer.id).first()
    cancelled = cancel_registration(db_session, registration)

    assert cancelled.status == RegistrationStatus.CANCELLED
    db_session.refresh(free_ticket_type)
    assert free_ticket_type.quantity_sold == 0


def test_cancel_registration_twice_raises(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)

    from app.models.order import Registration

    registration = db_session.query(Registration).filter_by(user_id=buyer.id).first()
    cancel_registration(db_session, registration)

    with pytest.raises(OrderServiceError):
        cancel_registration(db_session, registration)


def test_utcnow_naive_for_order_timestamps():
    assert utcnow().tzinfo is None


def test_check_in_registration_sets_status_and_timestamp(
    db_session, published_event, buyer, organizer, free_ticket_type
):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)

    from app.models.order import Registration

    registration = db_session.query(Registration).filter_by(user_id=buyer.id).first()

    checked_in = check_in_registration(
        db_session, published_event.id, registration.ticket_code, organizer
    )

    assert checked_in.status == RegistrationStatus.CHECKED_IN
    assert checked_in.checked_in_at is not None
    assert checked_in.checked_in_by_user_id == organizer.id


def test_check_in_registration_unknown_code_raises(db_session, published_event, organizer):
    with pytest.raises(OrderServiceError):
        check_in_registration(db_session, published_event.id, "DOESNOTEXIST", organizer)


def test_check_in_registration_twice_raises(
    db_session, published_event, buyer, organizer, free_ticket_type
):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)

    from app.models.order import Registration

    registration = db_session.query(Registration).filter_by(user_id=buyer.id).first()
    check_in_registration(db_session, published_event.id, registration.ticket_code, organizer)

    with pytest.raises(OrderServiceError):
        check_in_registration(db_session, published_event.id, registration.ticket_code, organizer)


def test_check_in_registration_cancelled_raises(
    db_session, published_event, buyer, organizer, free_ticket_type
):
    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)

    from app.models.order import Registration

    registration = db_session.query(Registration).filter_by(user_id=buyer.id).first()
    cancel_registration(db_session, registration)

    with pytest.raises(OrderServiceError):
        check_in_registration(db_session, published_event.id, registration.ticket_code, organizer)


def test_complete_order_free_enqueues_registration_complete_notification(
    db_session, published_event, buyer, free_ticket_type
):
    from app.models.notification import NotificationOutbox, NotificationTemplateKey

    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(free_ticket_type, session))
    complete_order(db_session, order)

    rows = db_session.query(NotificationOutbox).filter_by(user_id=buyer.id).all()
    assert len(rows) == 1
    assert rows[0].template_key == NotificationTemplateKey.REGISTRATION_COMPLETE


def test_complete_order_paid_enqueues_purchase_complete_notification(
    db_session, published_event, buyer, paid_ticket_type
):
    from app.models.notification import NotificationOutbox, NotificationTemplateKey

    session = published_event.sessions[0]
    order = create_order(db_session, buyer.id, _order_in(paid_ticket_type, session))
    complete_order(db_session, order)

    rows = db_session.query(NotificationOutbox).filter_by(user_id=buyer.id).all()
    assert len(rows) == 1
    assert rows[0].template_key == NotificationTemplateKey.TICKET_PURCHASE_COMPLETE
