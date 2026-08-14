from pydantic import BaseModel

from app.schemas.event import EventListItemOut
from app.schemas.instructor import InstructorOut


class OrganizerSummaryOut(BaseModel):
    id: int
    name: str
    follower_count: int


class HomeSectionsOut(BaseModel):
    popular_events: list[EventListItemOut]
    latest_events: list[EventListItemOut]
    featured_events: list[EventListItemOut]
    popular_instructors: list[InstructorOut]
    popular_organizers: list[OrganizerSummaryOut]
