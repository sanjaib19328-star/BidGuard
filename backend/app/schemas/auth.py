import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of the user")
    organization_name: str = Field(..., min_length=2, max_length=255, description="Organization / Department name")
    role: Optional[UserRole] = Field(
        default=UserRole.PROCUREMENT_OFFICER,
        description="Assigned role (public registration defaults to PROCUREMENT_OFFICER)",
    )


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token validity duration in seconds")


class TokenPayload(BaseModel):
    sub: str
    iat: Optional[int] = None
    exp: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    org_id: Optional[str] = None
