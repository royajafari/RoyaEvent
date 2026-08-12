from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.event import Event
from app.models.favorite import Favorite
from app.models.instructor import Instructor
from app.models.user import User
from app.services import social_service
from app.services.event_service import event_query, to_list_item_out

router = APIRouter(tags=["social"])


@router.post("/favorites/{event_id}")
def add_favorite(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if db.get(Event, event_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    favorited = social_service.toggle_favorite(db, current_user.id, event_id, add=True)
    return {"favorited": favorited}


@router.delete("/favorites/{event_id}")
def remove_favorite(
    event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    favorited = social_service.toggle_favorite(db, current_user.id, event_id, add=False)
    return {"favorited": favorited}


@router.get("/me/favorites")
def list_my_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event_ids = [f.event_id for f in db.query(Favorite).filter_by(user_id=current_user.id).all()]
    if not event_ids:
        return []
    events = event_query(db).filter(Event.id.in_(event_ids)).all()
    return [to_list_item_out(e) for e in events]


@router.post("/follows/organizers/{organizer_id}")
def follow_organizer(
    organizer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if db.get(User, organizer_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "برگزارکننده یافت نشد")
    following = social_service.toggle_organizer_follow(db, current_user.id, organizer_id, add=True)
    return {
        "following": following,
        "follower_count": social_service.organizer_follower_count(db, organizer_id),
    }


@router.delete("/follows/organizers/{organizer_id}")
def unfollow_organizer(
    organizer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    following = social_service.toggle_organizer_follow(db, current_user.id, organizer_id, add=False)
    return {
        "following": following,
        "follower_count": social_service.organizer_follower_count(db, organizer_id),
    }


@router.post("/follows/instructors/{instructor_id}")
def follow_instructor(
    instructor_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if db.get(Instructor, instructor_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مدرس یافت نشد")
    following = social_service.toggle_instructor_follow(db, current_user.id, instructor_id, add=True)
    return {
        "following": following,
        "follower_count": social_service.instructor_follower_count(db, instructor_id),
    }


@router.delete("/follows/instructors/{instructor_id}")
def unfollow_instructor(
    instructor_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    following = social_service.toggle_instructor_follow(db, current_user.id, instructor_id, add=False)
    return {
        "following": following,
        "follower_count": social_service.instructor_follower_count(db, instructor_id),
    }
