import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import Organization, User
from app.schemas.auth import TokenResponse, UserRegisterRequest


async def get_user_by_email(
    session: AsyncSession,
    email: str,
    include_organization: bool = True,
) -> Optional[User]:
    """Retrieve user by normalized email address."""
    normalized_email = email.lower().strip()
    query = select(User).where(func.lower(User.email) == normalized_email)
    if include_organization:
        query = query.options(selectinload(User.organization))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: uuid.UUID,
    include_organization: bool = True,
) -> Optional[User]:
    """Retrieve user by UUID."""
    query = select(User).where(User.id == user_id)
    if include_organization:
        query = query.options(selectinload(User.organization))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_or_create_organization(
    session: AsyncSession,
    org_name: str,
) -> Organization:
    """Resolve an existing organization by unique name or create a new one."""
    normalized_name = org_name.strip()
    query = select(Organization).where(func.lower(Organization.name) == normalized_name.lower())
    result = await session.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        org = Organization(name=normalized_name)
        session.add(org)
        await session.flush()

    return org


async def register_user(
    session: AsyncSession,
    req: UserRegisterRequest,
    allow_admin: bool = False,
) -> User:
    """Register a new user in PostgreSQL after validation and hashing."""
    normalized_email = req.email.lower().strip()

    # 1. Check duplicate user
    existing_user = await get_user_by_email(session, normalized_email, include_organization=False)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    # 2. Prevent unauthorized ADMIN role assignment during public registration
    assigned_role = req.role or UserRole.PROCUREMENT_OFFICER
    if assigned_role == UserRole.ADMIN and not allow_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public registration cannot create an ADMIN account. Please select a standard role.",
        )

    # 3. Resolve or create organization
    org = await get_or_create_organization(session, req.organization_name)

    # 4. Hash password securely
    hashed_password = get_password_hash(req.password)

    # 5. Create user record
    new_user = User(
        email=normalized_email,
        password_hash=hashed_password,
        full_name=req.full_name.strip(),
        role=assigned_role,
        organization_id=org.id,
        is_active=True,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user, attribute_names=["organization"])

    return new_user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """Verify credentials and return user if valid."""
    user = await get_user_by_email(session, email, include_organization=True)
    if not user:
        return None
    if not user.password_hash or not verify_password(password, user.password_hash):
        return None
    return user


def create_user_token(user: User) -> TokenResponse:
    """Generate a JWT bearer token for the authenticated user."""
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    extra_claims = {
        "email": user.email,
        "role": user.role.value,
        "org_id": str(user.organization_id),
    }
    token = create_access_token(
        subject=str(user.id),
        extra_claims=extra_claims,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in_seconds,
    )
