from datetime import datetime

from pydantic import BaseModel, Field


class EventReviewIn(BaseModel):
    axis_content_uptodate: int = Field(ge=0, le=5)
    axis_instructor_mastery: int = Field(ge=0, le=5)
    axis_value_for_price: int = Field(ge=0, le=5)
    axis_experience_driven: int = Field(ge=0, le=5)
    comment_text: str | None = Field(default=None, max_length=2000)


class EventReviewOut(BaseModel):
    id: int
    user_id: int
    user_name: str | None
    event_id: int
    axis_content_uptodate: int
    axis_instructor_mastery: int
    axis_value_for_price: int
    axis_experience_driven: int
    overall_computed: float
    comment_text: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
