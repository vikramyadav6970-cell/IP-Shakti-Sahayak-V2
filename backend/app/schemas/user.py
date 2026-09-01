"""
backend/app/schemas/user.py

Pydantic schemas for User entity representations and requests.
"""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.entities import RoleEnum


class UserRead(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: RoleEnum
    organization: Optional[str] = None
    language: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    organization: Optional[str] = None


class UserListResponse(BaseModel):
    items: List[UserRead]
    total: int
    page: int
    page_size: int
