"""امتیاز مدرس/برگزارکننده/سایت — ضربه‌ی ساده‌ی ۱-۵ ستاره، بدون محور
(برخلاف review_service.py که ۴محوره است). میانگین همیشه زنده محاسبه
می‌شه (نه denorm)، هم‌راستا با الگوی follower_count زنده‌ی این پروژه —
رول‌آپ شبانه صرفاً برای مقیاس بزرگ‌تر آینده در architecture.md پیش‌بینی
شده، نه نیاز فعلی."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.rating import InstructorRating, OrganizerRating, PlatformRating


def rate_instructor(db: Session, user_id: int, instructor_id: int, score: int) -> InstructorRating:
    rating = db.query(InstructorRating).filter_by(user_id=user_id, instructor_id=instructor_id).first()
    if rating is None:
        rating = InstructorRating(user_id=user_id, instructor_id=instructor_id, score=score)
        db.add(rating)
    else:
        rating.score = score
    db.commit()
    db.refresh(rating)
    return rating


def rate_organizer(db: Session, user_id: int, organizer_id: int, score: int) -> OrganizerRating:
    rating = db.query(OrganizerRating).filter_by(user_id=user_id, organizer_id=organizer_id).first()
    if rating is None:
        rating = OrganizerRating(user_id=user_id, organizer_id=organizer_id, score=score)
        db.add(rating)
    else:
        rating.score = score
    db.commit()
    db.refresh(rating)
    return rating


def rate_platform(db: Session, user_id: int, score: int) -> PlatformRating:
    rating = db.query(PlatformRating).filter_by(user_id=user_id).first()
    if rating is None:
        rating = PlatformRating(user_id=user_id, score=score)
        db.add(rating)
    else:
        rating.score = score
    db.commit()
    db.refresh(rating)
    return rating


def instructor_rating_stats(db: Session, instructor_id: int) -> tuple[float, int]:
    avg, count = (
        db.query(func.avg(InstructorRating.score), func.count(InstructorRating.id))
        .filter(InstructorRating.instructor_id == instructor_id)
        .one()
    )
    return (round(avg, 2) if avg is not None else 0.0, count)


def organizer_rating_stats(db: Session, organizer_id: int) -> tuple[float, int]:
    avg, count = (
        db.query(func.avg(OrganizerRating.score), func.count(OrganizerRating.id))
        .filter(OrganizerRating.organizer_id == organizer_id)
        .one()
    )
    return (round(avg, 2) if avg is not None else 0.0, count)


def platform_rating_stats(db: Session) -> tuple[float, int]:
    avg, count = db.query(func.avg(PlatformRating.score), func.count(PlatformRating.id)).one()
    return (round(avg, 2) if avg is not None else 0.0, count)


def my_instructor_rating(db: Session, user_id: int, instructor_id: int) -> int | None:
    rating = db.query(InstructorRating).filter_by(user_id=user_id, instructor_id=instructor_id).first()
    return rating.score if rating else None


def my_organizer_rating(db: Session, user_id: int, organizer_id: int) -> int | None:
    rating = db.query(OrganizerRating).filter_by(user_id=user_id, organizer_id=organizer_id).first()
    return rating.score if rating else None
