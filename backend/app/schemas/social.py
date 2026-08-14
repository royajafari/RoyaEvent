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
    avatar_url: str | None


class FollowedInstructorOut(BaseModel):
    id: int
    name: str
    avatar_url: str | None


class MyFollowsDetailOut(BaseModel):
    organizers: list[FollowedOrganizerOut]
    instructors: list[FollowedInstructorOut]


class FollowerUserOut(BaseModel):
    id: int
    name: str | None
    avatar_url: str | None


class MyFollowersOut(BaseModel):
    as_organizer: list[FollowerUserOut]
    as_instructor: list[FollowerUserOut]
