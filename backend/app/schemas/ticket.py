from typing import Literal

from pydantic import BaseModel, Field


class TicketTypeIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price: int = Field(ge=0, default=0)
    pricing_model: Literal["free", "paid", "donation"]
    quantity_total: int | None = Field(default=None, gt=0)
    is_early_bird: bool = False


class TicketTypeOut(BaseModel):
    id: int
    event_id: int
    name: str
    price: int
    pricing_model: str
    quantity_total: int | None
    quantity_sold: int
    is_early_bird: bool
    is_sold_out: bool
    is_early_bird_active: bool

    model_config = {"from_attributes": True}


class DiscountCodeIn(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    discount_type: Literal["percent", "fixed"]
    value: float = Field(gt=0)
    max_uses: int | None = Field(default=None, gt=0)
    valid_from: str | None = None
    valid_until: str | None = None


class DiscountCodeOut(BaseModel):
    id: int
    code: str
    discount_type: str
    value: float
    max_uses: int | None
    uses_count: int
    is_active: bool

    model_config = {"from_attributes": True}


class DiscountValidateIn(BaseModel):
    code: str
    event_id: int
