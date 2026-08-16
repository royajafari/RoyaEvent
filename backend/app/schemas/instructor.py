from pydantic import BaseModel

from app.schemas.event import EventListItemOut


class InstructorOut(BaseModel):
    id: int
    name: str
    bio: str | None
    avatar_url: str | None
    follower_count: int

    model_config = {"from_attributes": True}


class InstructorDetailOut(InstructorOut):
    is_following: bool
    is_claimed: bool
    is_owned_by_me: bool
    rating_avg: float
    rating_count: int
    my_rating: int | None
    events: list[EventListItemOut]
