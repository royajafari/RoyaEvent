from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.favorite import Favorite, InstructorFollow, OrganizerFollow


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


def organizer_follower_count(db: Session, organizer_id: int) -> int:
    return db.query(OrganizerFollow).filter_by(organizer_id=organizer_id).count()


def instructor_follower_count(db: Session, instructor_id: int) -> int:
    return db.query(InstructorFollow).filter_by(instructor_id=instructor_id).count()
