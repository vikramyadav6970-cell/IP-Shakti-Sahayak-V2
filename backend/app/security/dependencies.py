"""
backend/app/security/dependencies.py

FastAPI dependency injectors for authentication, user loading, and RBAC role validation.
"""

from typing import Callable, List, Optional
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import User, RoleEnum
from app.repositories.user_repository import UserRepository
from app.security.auth import decode_token

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates JWT bearer token and resolves the authenticated User.
    Raises 401 on invalid/expired token or missing credentials.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(auth.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token.",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return user


async def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolves the authenticated User if a valid JWT token is provided.
    If no token is provided, returns a persistent Guest User so that
    anonymous visitors and evaluators can test the AI consultation seamlessly.
    """
    if auth and auth.credentials:
        try:
            payload = decode_token(auth.credentials)
            if payload.get("type") == "access" and payload.get("sub"):
                user_repo = UserRepository(db)
                user = await user_repo.get_by_id(uuid.UUID(payload["sub"]))
                if user and user.is_active:
                    return user
        except Exception:
            pass

    # Ensure a Guest user account exists for unauthenticated consultation
    user_repo = UserRepository(db)
    guest_email = "guest@ipsakti.gov.in"
    guest_user = await user_repo.get_by_email(guest_email)
    if not guest_user:
        guest_user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            email=guest_email,
            name="Guest Innovator",
            role=RoleEnum.USER,
            hashed_password="guest_no_direct_login_allowed",
            is_active=True,
        )
        try:
            await user_repo.create(guest_user)
        except Exception:
            guest_user = await user_repo.get_by_email(guest_email) or guest_user
    return guest_user


def require_roles(*allowed_roles: RoleEnum) -> Callable:
    """
    Factory creating a dependency that gates endpoints to specific RBAC roles.
    Raises 403 Forbidden if user lacks permitted role.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != RoleEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of roles: {[r.value for r in allowed_roles]} (current: {current_user.role.value})",
            )
        return current_user

    return role_checker
