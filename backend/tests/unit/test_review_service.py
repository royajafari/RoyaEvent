from datetime import timedelta

import pytest

from app.models.base import utcnow
from app.models.review import ReviewStatus
from app.schemas.order import OrderCreateIn
from app.schemas.review import EventReviewIn
from app.services.order_service import complete_order, create_order
from app.services.review_service import (
    ReviewServiceError,
    list_event_reviews,
    set_review_hidden,
    submit_review,
)


def _review_in(**overrides) -> EventReviewIn:
    defaults = dict(
        axis_content_uptodate=5,
        axis_instructor_mastery=4,
        axis_value_for_price=3,
        axis_experience_driven=5,
    )
    defaults.update(overrides)
    return EventReviewIn(**defaults)


def _confirmed_registration(db_session, published_event, buyer, free_ticket_type):
    session = published_event.sessions[0]
    order = create_order(
        db_session, buyer.id, OrderCreateIn(ticket_type_id=free_ticket_type.id, session_id=session.id)
    )
    complete_order(db_session, order)


def test_submit_review_requires_registration(db_session, published_event, buyer):
    with pytest.raises(ReviewServiceError):
        submit_review(db_session, buyer.id, published_event.id, _review_in())


def test_submit_review_requires_session_already_started(
    db_session, published_event, buyer, free_ticket_type
):
    # published_event fixture جلسه‌ش رو تو آینده می‌سازه (هنوز شروع نشده)
    _confirmed_registration(db_session, published_event, buyer, free_ticket_type)

    with pytest.raises(ReviewServiceError):
        submit_review(db_session, buyer.id, published_event.id, _review_in())


def test_submit_review_success_updates_event_rating(
    db_session, published_event, buyer, free_ticket_type
):
    _confirmed_registration(db_session, published_event, buyer, free_ticket_type)
    published_event.sessions[0].starts_at = utcnow() - timedelta(hours=2)
    db_session.commit()

    review = submit_review(db_session, buyer.id, published_event.id, _review_in())

    assert review.overall_computed == pytest.approx((5 + 4 + 3 + 5) / 4)
    db_session.refresh(published_event)
    assert published_event.rating_avg == pytest.approx((5 + 4 + 3 + 5) / 4, rel=1e-2)
    assert published_event.rating_count == 1


def test_submit_review_twice_updates_not_duplicates(
    db_session, published_event, buyer, free_ticket_type
):
    _confirmed_registration(db_session, published_event, buyer, free_ticket_type)
    published_event.sessions[0].starts_at = utcnow() - timedelta(hours=2)
    db_session.commit()

    submit_review(db_session, buyer.id, published_event.id, _review_in())
    submit_review(db_session, buyer.id, published_event.id, _review_in(axis_content_uptodate=1))

    reviews = list_event_reviews(db_session, published_event.id)
    assert len(reviews) == 1
    assert reviews[0].axis_content_uptodate == 1


def test_set_review_hidden_excludes_from_list_and_recomputes_rating(
    db_session, published_event, buyer, free_ticket_type
):
    _confirmed_registration(db_session, published_event, buyer, free_ticket_type)
    published_event.sessions[0].starts_at = utcnow() - timedelta(hours=2)
    db_session.commit()

    review = submit_review(db_session, buyer.id, published_event.id, _review_in())
    set_review_hidden(db_session, review, hidden=True, reason="نامناسب")

    assert list_event_reviews(db_session, published_event.id) == []
    db_session.refresh(published_event)
    assert published_event.rating_count == 0
    assert published_event.rating_avg == 0.0

    unhidden = set_review_hidden(db_session, review, hidden=False, reason=None)
    assert unhidden.status == ReviewStatus.PUBLISHED
    assert len(list_event_reviews(db_session, published_event.id)) == 1
