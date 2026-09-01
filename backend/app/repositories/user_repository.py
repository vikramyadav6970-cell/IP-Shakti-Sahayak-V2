"""
backend/app/repositories/user_repository.py

Repository for User entity persistence operations.
"""

from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, RoleEnum


class UserRepository:
    """Encapsulates all database queries for User entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[RoleEnum] = None,
    ) -> Tuple[List[User], int]:
        query = select(User)
        count_query = select(func.count(User.id))

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        total_res = await self.session.execute(count_query)
        total = total_res.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        users = list(result.scalars().all())

        return users, total
