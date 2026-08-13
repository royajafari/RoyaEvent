from datetime import timedelta

from app.models.base import utcnow
from app.schemas.ticket import TicketTypeIn
from app.services import event_service, ticket_service


def test_early_bird_active_right_after_publish(published_event):
    """طبق نیازمندی ۳۴: بلافاصله بعد از باز شدن فروش، هنوز کمتر از یک‌سوم
    بازه گذشته، پس بلیط زودهنگام باید فعال باشد."""
    assert ticket_service.is_early_bird_active(published_event) is True


def test_early_bird_inactive_after_window_passed(db_session, published_event):
    # جلسه ۱۰ روز دیگه شروع می‌شه؛ وانمود می‌کنیم فروش از ۸ روز قبل باز بوده
    # (بازه‌ی کل ~۱۸ روز، ۸ روز گذشته > یک‌سوم بازه یعنی ~۶ روز)
    published_event.published_at = utcnow() - timedelta(days=8)
    db_session.commit()

    assert ticket_service.is_early_bird_active(published_event) is False


def test_early_bird_inactive_without_published_or_sales_open_at(db_session, leaf_category, organizer):
    from datetime import datetime

    from app.schemas.event import EventCreateIn, EventSessionIn

    data = EventCreateIn(
        title="رویداد پیش‌نویس",
        description="توضیحات",
        category_id=leaf_category.id,
        format="online",
        online_platform_name="SkyRoom",
        sessions=[EventSessionIn(starts_at=datetime.now() + timedelta(days=5), duration_minutes=60)],
    )
    draft_event = event_service.create_event(db_session, organizer.id, data)
    assert draft_event.published_at is None

    assert ticket_service.is_early_bird_active(draft_event) is False


def test_early_bird_inactive_when_no_sessions(db_session, published_event):
    published_event.sessions.clear()
    db_session.commit()
    assert ticket_service.is_early_bird_active(published_event) is False


def test_create_ticket_type_free_forces_zero_price(db_session, published_event):
    data = TicketTypeIn(name="بلیط رایگان", pricing_model="free", price=50000)
    ticket_type = ticket_service.create_ticket_type(db_session, published_event, data)
    assert ticket_type.price == 0


def test_create_ticket_type_paid_keeps_price(db_session, published_event):
    data = TicketTypeIn(name="بلیط ویژه", pricing_model="paid", price=99000)
    ticket_type = ticket_service.create_ticket_type(db_session, published_event, data)
    assert ticket_type.price == 99000


def test_to_ticket_type_out_reports_sold_out(db_session, published_event):
    data = TicketTypeIn(name="بلیط محدود", pricing_model="free", quantity_total=1)
    ticket_type = ticket_service.create_ticket_type(db_session, published_event, data)
    assert ticket_service.to_ticket_type_out(ticket_type, published_event).is_sold_out is False

    ticket_type.quantity_sold = 1
    db_session.commit()
    assert ticket_service.to_ticket_type_out(ticket_type, published_event).is_sold_out is True


def test_to_ticket_type_out_early_bird_flag_only_when_marked(db_session, published_event):
    data = TicketTypeIn(name="بلیط عادی", pricing_model="free", is_early_bird=False)
    ticket_type = ticket_service.create_ticket_type(db_session, published_event, data)
    out = ticket_service.to_ticket_type_out(ticket_type, published_event)
    assert out.is_early_bird is False
    assert out.is_early_bird_active is False


def test_utcnow_used_for_elapsed_is_naive():
    # اطمینان از سازگاری با ستون‌های naive UTC (بخش «قراردادهای API» در CLAUDE.md)
    assert utcnow().tzinfo is None
