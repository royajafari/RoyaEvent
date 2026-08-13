from pydantic import BaseModel

from app.schemas.event import EventListItemOut


class FavoriteOut(BaseModel):
    event: EventListItemOut


class FollowStatusOut(BaseModel):
    following: bool
    follower_count: int


class FollowedOrganizerOut(BaseModel):
    id: int
    name: str | None


class FollowedInstructorOut(BaseModel):
    id: int
    name: str
    avatar_url: str | None


class MyFollowsDetailOut(BaseModel):
    organizers: list[FollowedOrganizerOut]
    instructors: list[FollowedInstructorOut]
