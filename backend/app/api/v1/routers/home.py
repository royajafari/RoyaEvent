from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_redis
from app.schemas.home import HomeSectionsOut
from app.services import home_service

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/sections", response_model=HomeSectionsOut)
def get_sections(db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return home_service.get_home_sections(db, redis_client)
