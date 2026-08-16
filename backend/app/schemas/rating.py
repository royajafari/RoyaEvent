from typing import Literal

from pydantic import BaseModel, Field


class RatingIn(BaseModel):
    entity_type: Literal["instructor", "organizer", "platform"]
    entity_id: int | None = None
    score: int = Field(ge=1, le=5)


class RatingOut(BaseModel):
    score: int
    average: float
    count: int
