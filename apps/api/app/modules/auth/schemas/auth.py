"""Auth request/response schemas."""

from pydantic import BaseModel, Field


class SendOTPRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=15, examples=["+919800000001"])


class VerifyOTPRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=4, max_length=8)


class PasswordLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    school_id: str
    full_name: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str
