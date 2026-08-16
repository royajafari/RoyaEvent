from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit_middleware import limiter
from app.models.instructor import Instructor
from app.models.user import User
from app.schemas.rating import RatingIn, RatingOut
from app.services import rating_service

router = APIRouter(tags=["ratings"])


@router.post("/ratings", response_model=RatingOut)
@limiter.limit("20/minute")
def submit_rating(
    request: Request,
    body: RatingIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.entity_type == "instructor":
        if body.entity_id is None or db.get(Instructor, body.entity_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "مدرس یافت نشد")
        rating_service.rate_instructor(db, current_user.id, body.entity_id, body.score)
        average, count = rating_service.instructor_rating_stats(db, body.entity_id)
    elif body.entity_type == "organizer":
        if body.entity_id is None or db.get(User, body.entity_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "برگزارکننده یافت نشد")
        rating_service.rate_organizer(db, current_user.id, body.entity_id, body.score)
        average, count = rating_service.organizer_rating_stats(db, body.entity_id)
    else:
        rating_service.rate_platform(db, current_user.id, body.score)
        average, count = rating_service.platform_rating_stats(db)

    return RatingOut(score=body.score, average=average, count=count)
