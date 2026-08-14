from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus, EventVisibility
from app.models.favorite import InstructorFollow
from app.models.instructor import Instructor
from app.services.event_service import event_query


class InstructorServiceError(ValueError):
    pass


def claim_instructor(db: Session, instructor: Instructor, user_id: int) -> Instructor:
    """کاربر خودش پروفایل مدرس رو claim می‌کنه (تصمیم کاربر) — بدون این،
    linked_user_id هیچ‌وقت پر نمی‌شد و سیستم راهی نداشت بفهمه کدوم کاربر
    لاگین‌کرده معادل کدوم رکورد Instructor است (لازم برای دیدن
    دنبال‌کننده‌های خودش، social_service.list_my_followers)."""
    if instructor.linked_user_id is not None:
        raise InstructorServiceError("این پروفایل مدرس قبلاً توسط یک کاربر claim شده است")
    instructor.linked_user_id = user_id
    db.commit()
    db.refresh(instructor)
    return instructor


def list_popular_instructors(db: Session, limit: int = 12) -> list[tuple[Instructor, int]]:
    """مدرس‌های محبوب برای بخش صفحه‌ی اصلی — MVP: مرتب‌سازی زنده بر اساس
    follower_count (رول‌آپ شبانه‌ی popularity_score جزو فاز ۴/۸ آینده‌ست،
    فعلاً over-engineering نیست چون تعداد مدرس‌ها کمه)."""
    rows = (
        db.query(Instructor, func.count(InstructorFollow.follower_user_id))
        .outerjoin(InstructorFollow, InstructorFollow.instructor_id == Instructor.id)
        .group_by(Instructor.id)
        .order_by(func.count(InstructorFollow.follower_user_id).desc(), Instructor.name)
        .limit(limit)
        .all()
    )
    return [(instructor, count) for instructor, count in rows]


def instructor_follower_count(db: Session, instructor_id: int) -> int:
    return db.query(InstructorFollow).filter_by(instructor_id=instructor_id).count()


def instructor_published_events(db: Session, instructor_id: int) -> list[Event]:
    return (
        event_query(db)
        .filter(
            Event.instructors.any(Instructor.id == instructor_id),
            Event.status == EventStatus.PUBLISHED,
            Event.visibility == EventVisibility.PUBLIC,
        )
        .order_by(Event.published_at.desc())
        .all()
    )
