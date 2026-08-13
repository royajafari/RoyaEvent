from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.favorite import Favorite, InstructorFollow, OrganizerFollow
from app.models.instructor import Instructor
from app.models.user import User


def toggle_favorite(db: Session, user_id: int, event_id: int, *, add: bool) -> bool:
    existing = db.query(Favorite).filter_by(user_id=user_id, event_id=event_id).first()
    if add:
        if existing is None:
            db.add(Favorite(user_id=user_id, event_id=event_id))
            db.commit()
        return True
    if existing is not None:
        db.delete(existing)
        db.commit()
    return False


def toggle_organizer_follow(db: Session, follower_user_id: int, organizer_id: int, *, add: bool) -> bool:
    existing = (
        db.query(OrganizerFollow)
        .filter_by(follower_user_id=follower_user_id, organizer_id=organizer_id)
        .first()
    )
    if add:
        if existing is None:
            db.add(OrganizerFollow(follower_user_id=follower_user_id, organizer_id=organizer_id))
            db.commit()
        return True
    if existing is not None:
        db.delete(existing)
        db.commit()
    return False


def toggle_instructor_follow(db: Session, follower_user_id: int, instructor_id: int, *, add: bool) -> bool:
    existing = (
        db.query(InstructorFollow)
        .filter_by(follower_user_id=follower_user_id, instructor_id=instructor_id)
        .first()
    )
    if add:
        if existing is None:
            db.add(InstructorFollow(follower_user_id=follower_user_id, instructor_id=instructor_id))
            db.commit()
        return True
    if existing is not None:
        db.delete(existing)
        db.commit()
    return False


def list_my_follows(db: Session, follower_user_id: int) -> dict[str, list[int]]:
    organizer_ids = [
        f.organizer_id
        for f in db.query(OrganizerFollow).filter_by(follower_user_id=follower_user_id).all()
    ]
    instructor_ids = [
        f.instructor_id
        for f in db.query(InstructorFollow).filter_by(follower_user_id=follower_user_id).all()
    ]
    return {"organizer_ids": organizer_ids, "instructor_ids": instructor_ids}


def list_my_follows_detail(db: Session, follower_user_id: int) -> dict:
    """نسخه‌ی enrich‌شده‌ی list_my_follows برای صفحه‌ی «دنبال‌کردن‌های من» —
    برخلاف اون که فقط id برمی‌گردونه (برای وضعیت دکمه‌ی toggle کافیه)،
    اینجا اسم/آواتار لازمه که چیزی برای نمایش داشته باشیم."""
    organizer_ids = [
        f.organizer_id
        for f in db.query(OrganizerFollow).filter_by(follower_user_id=follower_user_id).all()
    ]
    instructor_ids = [
        f.instructor_id
        for f in db.query(InstructorFollow).filter_by(follower_user_id=follower_user_id).all()
    ]

    organizers = db.query(User).filter(User.id.in_(organizer_ids)).all() if organizer_ids else []
    instructors = (
        db.query(Instructor).filter(Instructor.id.in_(instructor_ids)).all() if instructor_ids else []
    )

    return {
        "organizers": [
            {"id": u.id, "name": u.full_name or u.phone or u.email} for u in organizers
        ],
        "instructors": [
            {"id": i.id, "name": i.name, "avatar_url": i.avatar_url} for i in instructors
        ],
    }


def organizer_follower_count(db: Session, organizer_id: int) -> int:
    return db.query(OrganizerFollow).filter_by(organizer_id=organizer_id).count()


def instructor_follower_count(db: Session, instructor_id: int) -> int:
    return db.query(InstructorFollow).filter_by(instructor_id=instructor_id).count()
