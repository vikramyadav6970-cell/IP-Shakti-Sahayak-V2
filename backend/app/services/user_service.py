"""
backend/app/services/user_service.py

User profile management and admin user querying.
"""

from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, RoleEnum
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead, UserUpdate, UserListResponse


class UserService:
    """Business logic for user accounts."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserRead:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return UserRead.model_validate(user)

    async def update_profile(self, user: User, update_data: UserUpdate) -> UserRead:
        if update_data.name is not None:
            user.name = update_data.name.strip()
        if update_data.language is not None:
            user.language = update_data.language.strip()
        if update_data.organization is not None:
            user.organization = update_data.organization.strip()

        await self.session.commit()
        await self.session.refresh(user)
        return UserRead.model_validate(user)

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[RoleEnum] = None,
    ) -> UserListResponse:
        users, total = await self.user_repo.list_users(page=page, page_size=page_size, role=role)
        return UserListResponse(
            items=[UserRead.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
        )
