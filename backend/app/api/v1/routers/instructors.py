from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.core.permissions import require_complete_profile
from app.models.favorite import InstructorFollow
from app.models.instructor import Instructor
from app.models.user import User
from app.schemas.instructor import InstructorDetailOut, InstructorOut
from app.services import instructor_service
from app.services.event_service import to_list_item_out
from app.services.instructor_service import InstructorServiceError

router = APIRouter(prefix="/instructors", tags=["instructors"])


def _build_detail_out(db: Session, instructor: Instructor, current_user: User | None) -> InstructorDetailOut:
    is_following = False
    if current_user is not None:
        is_following = (
            db.query(InstructorFollow)
            .filter_by(follower_user_id=current_user.id, instructor_id=instructor.id)
            .first()
            is not None
        )

    events = instructor_service.instructor_published_events(db, instructor.id)
    return InstructorDetailOut(
        id=instructor.id,
        name=instructor.name,
        bio=instructor.bio,
        avatar_url=instructor.avatar_url,
        follower_count=instructor_service.instructor_follower_count(db, instructor.id),
        is_following=is_following,
        is_claimed=instructor.linked_user_id is not None,
        is_owned_by_me=current_user is not None and instructor.linked_user_id == current_user.id,
        events=[to_list_item_out(e) for e in events],
    )


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
    return _build_detail_out(db, instructor, current_user)


@router.post("/{instructor_id}/claim", response_model=InstructorDetailOut)
def claim_instructor(
    instructor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_complete_profile(current_user)
    instructor = db.get(Instructor, instructor_id)
    if instructor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مدرس یافت نشد")
    try:
        instructor_service.claim_instructor(db, instructor, current_user.id)
    except InstructorServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return _build_detail_out(db, instructor, current_user)
