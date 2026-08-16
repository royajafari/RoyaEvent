from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.models.favorite import OrganizerFollow
from app.models.user import User
from app.schemas.organizer import OrganizerProfileOut
from app.services import organizer_service, rating_service
from app.services.event_service import to_list_item_out
from app.services.social_service import organizer_follower_count

router = APIRouter(prefix="/organizers", tags=["organizers"])


@router.get("/{organizer_id}", response_model=OrganizerProfileOut)
def get_organizer_profile(
    organizer_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    organizer = db.get(User, organizer_id)
    if organizer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "برگزارکننده یافت نشد")

    is_following = False
    if current_user is not None:
        is_following = (
            db.query(OrganizerFollow)
            .filter_by(follower_user_id=current_user.id, organizer_id=organizer_id)
            .first()
            is not None
        )

    events = organizer_service.organizer_published_events(db, organizer_id)
    rating_avg, rating_count = rating_service.organizer_rating_stats(db, organizer_id)
    my_rating = (
        rating_service.my_organizer_rating(db, current_user.id, organizer_id)
        if current_user is not None
        else None
    )
    return OrganizerProfileOut(
        id=organizer.id,
        name=organizer.full_name or organizer.phone or organizer.email,
        avatar_url=organizer.avatar_url,
        follower_count=organizer_follower_count(db, organizer_id),
        is_following=is_following,
        rating_avg=rating_avg,
        rating_count=rating_count,
        my_rating=my_rating,
        events=[to_list_item_out(e) for e in events],
    )
