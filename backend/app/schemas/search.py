from typing import Literal

from pydantic import BaseModel

from app.schemas.event import EventListItemOut


class PersonResultOut(BaseModel):
    type: Literal["organizer", "instructor"]
    id: int
    name: str
    avatar_url: str | None


class SearchResultOut(BaseModel):
    people: list[PersonResultOut]
    events: list[EventListItemOut]


class SearchSuggestionsOut(BaseModel):
    suggestions: list[str]
