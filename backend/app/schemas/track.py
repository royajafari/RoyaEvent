from typing import Literal

from pydantic import BaseModel, Field

TrackEventType = Literal["page_view", "search_query", "funnel_step", "click"]


class TrackEventIn(BaseModel):
    """بیکن سبک فرانت (بخش ۱۱ پلن) — payload آزاده چون هر ۴ کالکشن Mongo
    شکل فیلد متفاوتی دارن (page_views vs funnel_events و...)."""

    event_type: TrackEventType
    session_id: str = Field(min_length=1, max_length=100)
    payload: dict = Field(default_factory=dict)
