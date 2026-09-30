import uuid
from typing import Any, Callable, Optional, Sequence
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import get_user_by_id

# OAuth2 bearer token extractor
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    scheme_name="JWT Bearer",
    description="JWT Bearer Token authentication",
    auto_error=True,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT token and return the authenticated active user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await get_user_by_id(session, user_id=user_id, include_organization=True)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user


oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    scheme_name="JWT Bearer",
    description="JWT Bearer Token authentication",
    auto_error=False,
)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT token if provided; otherwise return default demo procurement officer."""
    if not token:
        return User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            email="officer@cag.gov.in",
            full_name="Procurement Officer (CAG)",
            role=UserRole.PROCUREMENT_OFFICER,
            is_active=True,
        )

    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401)
        user_id = uuid.UUID(user_id_str)
        user = await get_user_by_id(session, user_id=user_id, include_organization=True)
        if user and user.is_active:
            return user
    except Exception:
        pass

    return User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="officer@cag.gov.in",
        full_name="Procurement Officer (CAG)",
        role=UserRole.PROCUREMENT_OFFICER,
        is_active=True,
    )



def require_roles(*roles: Any) -> Callable:
    """Enforce exact RBAC permissions against the authenticated user.
    
    If multiple roles are supplied (either as individual arguments or as a sequence),
    the user's role must match one of the allowed roles.
    Does not assume implicit inheritance.
    """
    flattened_roles = []
    for r in roles:
        if isinstance(r, (list, tuple, set)):
            flattened_roles.extend(r)
        else:
            flattened_roles.append(r)
    allowed_roles = tuple(flattened_roles)

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of [{', '.join(role_names)}] role.",
            )
        return current_user

    return role_checker


# Exact role dependencies (no implicit inheritance)
require_admin = require_roles(UserRole.ADMIN)
require_procurement_officer = require_roles(UserRole.PROCUREMENT_OFFICER)
require_reviewer = require_roles(UserRole.REVIEWER)
require_auditor = require_roles(UserRole.AUDITOR)
