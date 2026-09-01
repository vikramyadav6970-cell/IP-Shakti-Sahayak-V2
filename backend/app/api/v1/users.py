"""
backend/app/api/v1/users.py

User profile and administration endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import User, RoleEnum
from app.schemas.user import UserRead, UserUpdate, UserListResponse
from app.security.dependencies import get_current_user, require_roles
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get profile of the currently authenticated user",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Returns the authenticated user's profile."""
    return UserRead.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update profile of the currently authenticated user",
)
async def update_my_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates editable profile fields (name, language, organization)."""
    service = UserService(db)
    return await service.update_profile(current_user, req)


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin only)",
)
async def list_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[RoleEnum] = None,
    _admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Paginated user directory, restricted to ADMIN users."""
    service = UserService(db)
    return await service.list_users(page=page, page_size=page_size, role=role)
