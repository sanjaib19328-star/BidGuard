from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    require_admin,
    require_auditor,
    require_procurement_officer,
    require_reviewer,
    require_roles,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_user_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a user and provisions / associates them with an organization in PostgreSQL.",
)
async def register(
    req: UserRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user account."""
    user = await register_user(session, req, allow_admin=False)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login (JSON Body)",
    description="Authenticates with email and password, returning a signed JWT Bearer access token.",
)
async def login(
    req: UserLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate via JSON payload and retrieve a JWT access token."""
    user = await authenticate_user(session, email=req.email, password=req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return create_user_token(user)


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 Password Form Token",
    description="Standard OAuth2 password flow endpoint for Swagger UI and compatible clients.",
)
async def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate via OAuth2 Form data and retrieve a JWT access token."""
    user = await authenticate_user(
        session,
        email=form_data.username,
        password=form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username (email) or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return create_user_token(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the profile and organization details of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve details for the active authenticated user."""
    return current_user


# ==============================================================================
# Isolated RBAC Test & Verification Endpoints (Development / Test Verification Only)
# ==============================================================================

@router.get(
    "/test-rbac/admin-only",
    summary="[TEST ONLY] Admin-only route",
    description="Development verification endpoint accessible strictly by ADMIN role.",
)
async def test_rbac_admin(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    return {
        "status": "authorized",
        "role_required": "ADMIN",
        "user_email": current_user.email,
        "user_role": current_user.role.value,
    }


@router.get(
    "/test-rbac/officer-only",
    summary="[TEST ONLY] Procurement Officer-only route",
    description="Development verification endpoint accessible strictly by PROCUREMENT_OFFICER role.",
)
async def test_rbac_officer(
    current_user: User = Depends(require_procurement_officer),
) -> Dict[str, Any]:
    return {
        "status": "authorized",
        "role_required": "PROCUREMENT_OFFICER",
        "user_email": current_user.email,
        "user_role": current_user.role.value,
    }


@router.get(
    "/test-rbac/reviewer-only",
    summary="[TEST ONLY] Reviewer-only route",
    description="Development verification endpoint accessible strictly by REVIEWER role.",
)
async def test_rbac_reviewer(
    current_user: User = Depends(require_reviewer),
) -> Dict[str, Any]:
    return {
        "status": "authorized",
        "role_required": "REVIEWER",
        "user_email": current_user.email,
        "user_role": current_user.role.value,
    }


@router.get(
    "/test-rbac/auditor-only",
    summary="[TEST ONLY] Auditor-only route",
    description="Development verification endpoint accessible strictly by AUDITOR role.",
)
async def test_rbac_auditor(
    current_user: User = Depends(require_auditor),
) -> Dict[str, Any]:
    return {
        "status": "authorized",
        "role_required": "AUDITOR",
        "user_email": current_user.email,
        "user_role": current_user.role.value,
    }


@router.get(
    "/test-rbac/admin-or-officer",
    summary="[TEST ONLY] Admin or Officer multi-role route",
    description="Development verification endpoint accessible by ADMIN or PROCUREMENT_OFFICER explicitly.",
)
async def test_rbac_admin_or_officer(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER)),
) -> Dict[str, Any]:
    return {
        "status": "authorized",
        "role_required": "ADMIN or PROCUREMENT_OFFICER",
        "user_email": current_user.email,
        "user_role": current_user.role.value,
    }
