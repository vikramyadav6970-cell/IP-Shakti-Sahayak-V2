"""
backend/app/schemas/auth.py

Pydantic schemas for authentication and tokens.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.entities import RoleEnum


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[RoleEnum] = Field(default=RoleEnum.USER)
    organization: Optional[str] = None
    language: Optional[str] = "en"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str  # User UUID
    email: str
    role: RoleEnum
    type: str
    exp: int
