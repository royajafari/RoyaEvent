from typing import Literal

from pydantic import BaseModel, Field


class OTPRequestIn(BaseModel):
    channel: Literal["sms", "email"]
    destination: str = Field(min_length=3, max_length=255)
    purpose: Literal["login", "add_contact_channel"] = "login"


class OTPRequestOut(BaseModel):
    success: bool = True
    challenge_id: int
    expires_in: int
    retry_after: int


class OTPVerifyIn(BaseModel):
    challenge_id: int
    otp: str = Field(min_length=4, max_length=8)


class OTPVerifyOut(BaseModel):
    success: bool
    verified: bool
    access_token: str | None = None
    token_type: str | None = None
    message: str | None = None


class OTPResendIn(BaseModel):
    challenge_id: int


class UserOut(BaseModel):
    id: int
    phone: str | None
    email: str | None
    full_name: str | None
    avatar_url: str | None
    role: str
    status: str

    model_config = {"from_attributes": True}


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdateIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
