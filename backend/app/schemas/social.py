from pydantic import BaseModel

from app.schemas.event import EventListItemOut


class FavoriteOut(BaseModel):
    event: EventListItemOut


class FollowStatusOut(BaseModel):
    following: bool
    follower_count: int
