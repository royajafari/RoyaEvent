"""نظر ۴محوره رویداد — بخش ۳ پلن معماری. تصمیم کاربر (#۲): این خودِ
منبع events.rating_avg است، نه یه مکانیزم امتیازدهی جدا."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.event import Event, EventSession
from app.models.order import Registration, RegistrationStatus
from app.models.review import EventReview, ReviewStatus
from app.schemas.review import EventReviewIn


class ReviewServiceError(ValueError):
    pass


def _find_eligible_registration(db: Session, user_id: int, event_id: int) -> Registration:
    """گیت: فقط شرکت‌کننده‌ی واقعی — یه ثبت‌نام تأییدشده برای جلسه‌ای که
    واقعاً شروع شده باشه (نمی‌شه قبل از برگزاری رویداد نظر داد)."""
    registration = (
        db.query(Registration)
        .join(EventSession, EventSession.id == Registration.session_id)
        .filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id,
            Registration.status == RegistrationStatus.CONFIRMED,
            EventSession.starts_at <= utcnow(),
        )
        .order_by(EventSession.starts_at.desc())
        .first()
    )
    if registration is None:
        raise ReviewServiceError(
            "فقط شرکت‌کنندگان واقعی این رویداد (بعد از شروع جلسه) می‌توانند نظر ثبت کنند"
        )
    return registration


def _recompute_event_rating(db: Session, event_id: int) -> None:
    avg_rating, count = (
        db.query(func.avg(EventReview.overall_computed), func.count(EventReview.id))
        .filter(EventReview.event_id == event_id, EventReview.status == ReviewStatus.PUBLISHED)
        .one()
    )
    event = db.get(Event, event_id)
    event.rating_avg = round(avg_rating, 2) if avg_rating is not None else 0.0
    event.rating_count = count


def submit_review(db: Session, user_id: int, event_id: int, data: EventReviewIn) -> EventReview:
    """create-or-update: کاربر می‌تونه نظرش رو بعداً ویرایش کنه (unique(user_id,event_id))."""
    registration = _find_eligible_registration(db, user_id, event_id)

    axes = [
        data.axis_content_uptodate,
        data.axis_instructor_mastery,
        data.axis_value_for_price,
        data.axis_experience_driven,
    ]
    overall = sum(axes) / len(axes)

    review = db.query(EventReview).filter_by(user_id=user_id, event_id=event_id).first()
    if review is None:
        review = EventReview(user_id=user_id, event_id=event_id)
        db.add(review)

    review.registration_id = registration.id
    review.axis_content_uptodate = data.axis_content_uptodate
    review.axis_instructor_mastery = data.axis_instructor_mastery
    review.axis_value_for_price = data.axis_value_for_price
    review.axis_experience_driven = data.axis_experience_driven
    review.overall_computed = overall
    review.comment_text = data.comment_text
    review.status = ReviewStatus.PUBLISHED

    db.flush()
    _recompute_event_rating(db, event_id)
    db.commit()
    db.refresh(review)
    return review


def list_event_reviews(db: Session, event_id: int) -> list[EventReview]:
    return (
        db.query(EventReview)
        .filter(EventReview.event_id == event_id, EventReview.status == ReviewStatus.PUBLISHED)
        .order_by(EventReview.created_at.desc())
        .all()
    )


def set_review_hidden(db: Session, review: EventReview, *, hidden: bool, reason: str | None) -> EventReview:
    review.status = ReviewStatus.HIDDEN if hidden else ReviewStatus.PUBLISHED
    review.hidden_reason = reason if hidden else None
    db.flush()
    _recompute_event_rating(db, review.event_id)
    db.commit()
    db.refresh(review)
    return review
