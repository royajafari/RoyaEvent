from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.models.favorite import InstructorFollow
from app.models.instructor import Instructor
from app.models.user import User
from app.schemas.instructor import InstructorDetailOut, InstructorOut
from app.services import instructor_service
from app.services.event_service import to_list_item_out

router = APIRouter(prefix="/instructors", tags=["instructors"])


@router.get("", response_model=list[InstructorOut])
def list_popular_instructors(db: Session = Depends(get_db)):
    rows = instructor_service.list_popular_instructors(db)
    return [
        InstructorOut(
            id=instructor.id,
            name=instructor.name,
            bio=instructor.bio,
            avatar_url=instructor.avatar_url,
            follower_count=follower_count,
        )
        for instructor, follower_count in rows
    ]


@router.get("/{instructor_id}", response_model=InstructorDetailOut)
def get_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    instructor = db.get(Instructor, instructor_id)
    if instructor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مدرس یافت نشد")

    is_following = False
    if current_user is not None:
        is_following = (
            db.query(InstructorFollow)
            .filter_by(follower_user_id=current_user.id, instructor_id=instructor_id)
            .first()
            is not None
        )

    events = instructor_service.instructor_published_events(db, instructor_id)
    return InstructorDetailOut(
        id=instructor.id,
        name=instructor.name,
        bio=instructor.bio,
        avatar_url=instructor.avatar_url,
        follower_count=instructor_service.instructor_follower_count(db, instructor_id),
        is_following=is_following,
        events=[to_list_item_out(e) for e in events],
    )
