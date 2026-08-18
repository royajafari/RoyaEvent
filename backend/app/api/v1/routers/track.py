from fastapi import APIRouter, Depends, Request, Response
from pymongo.database import Database

from app.api.deps import get_client_ip, get_current_user_optional, get_mongo_db
from app.core.rate_limit_middleware import limiter
from app.models.user import User
from app.schemas.track import TrackEventIn
from app.services import track_service

router = APIRouter(prefix="/track", tags=["track"])


@router.post("", status_code=204)
@limiter.limit("120/minute")
def track_event(
    request: Request,
    body: TrackEventIn,
    mongo_db: Database = Depends(get_mongo_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    track_service.record_event(
        mongo_db,
        body.event_type,
        body.session_id,
        current_user.id if current_user else None,
        get_client_ip(request),
        body.payload,
    )
    return Response(status_code=204)
