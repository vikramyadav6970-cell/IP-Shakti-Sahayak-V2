"""
backend/app/api/v1/auth.py

Authentication route handlers (register, login, refresh).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new user account with role defaults.
    """
    service = AuthService(db)
    user = await service.register(req)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and obtain JWT access and refresh tokens",
)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates credentials and returns JWT bearer tokens.
    """
    service = AuthService(db)
    return await service.login(req)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using valid refresh token",
)
async def refresh_token(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Issues a new access token given a valid refresh token.
    """
    service = AuthService(db)
    return await service.refresh(req)
