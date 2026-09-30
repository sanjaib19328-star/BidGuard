import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.enums import UserRole
from app.models.user import Organization, User


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_user_registration_success(test_client):
    """Verify standard user registration with new organization in PostgreSQL."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"officer_{unique_id}@example.com"
    payload = {
        "email": email,
        "password": "SecurePassword123!",
        "full_name": f"Officer {unique_id}",
        "organization_name": f"GeM Department {unique_id}",
        "role": "PROCUREMENT_OFFICER",
    }

    response = await test_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == email.lower()
    assert data["full_name"] == f"Officer {unique_id}"
    assert data["role"] == "PROCUREMENT_OFFICER"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data
    assert data["organization"]["name"] == f"GeM Department {unique_id}"


@pytest.mark.asyncio
async def test_user_registration_existing_organization(test_client):
    """Verify second user registering under an already existing organization."""
    unique_id = uuid.uuid4().hex[:8]
    org_name = f"Common Dept {unique_id}"
    
    # First user
    payload1 = {
        "email": f"user1_{unique_id}@example.com",
        "password": "Password1234!",
        "full_name": "First User",
        "organization_name": org_name,
        "role": "PROCUREMENT_OFFICER",
    }
    res1 = await test_client.post("/api/v1/auth/register", json=payload1)
    assert res1.status_code == 201
    org1_id = res1.json()["organization_id"]

    # Second user in same organization
    payload2 = {
        "email": f"user2_{unique_id}@example.com",
        "password": "Password1234!",
        "full_name": "Second User",
        "organization_name": org_name.upper(),  # case-insensitive match
        "role": "REVIEWER",
    }
    res2 = await test_client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 201
    assert res2.json()["organization_id"] == org1_id


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(test_client):
    """Verify duplicate email registration is rejected with 400."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"dup_{unique_id}@example.com"
    payload = {
        "email": email,
        "password": "Password1234!",
        "full_name": "Duplicate User",
        "organization_name": f"Dept {unique_id}",
    }

    res1 = await test_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await test_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_user_registration_disallow_public_admin(test_client):
    """Verify direct public registration with ADMIN role is rejected with 400."""
    unique_id = uuid.uuid4().hex[:8]
    payload = {
        "email": f"admin_attempt_{unique_id}@example.com",
        "password": "Password1234!",
        "full_name": "Hacker Admin",
        "organization_name": "Gov Org",
        "role": "ADMIN",
    }
    response = await test_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "ADMIN" in response.json()["detail"]


@pytest.mark.asyncio
async def test_user_registration_validation_errors(test_client):
    """Verify validation errors for short password and invalid email."""
    # Short password (< 8 chars)
    res_short = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@example.com",
            "password": "short",
            "full_name": "Test User",
            "organization_name": "Dept",
        },
    )
    assert res_short.status_code == 422

    # Invalid email
    res_email = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "ValidPassword123!",
            "full_name": "Test User",
            "organization_name": "Dept",
        },
    )
    assert res_email.status_code == 422


@pytest.mark.asyncio
async def test_login_and_token_flow(test_client):
    """Verify JSON login and OAuth2 password form login return valid tokens."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"login_{unique_id}@example.com"
    password = "LoginPass123!"

    # 1. Register
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login Test User",
            "organization_name": f"Dept {unique_id}",
            "role": "PROCUREMENT_OFFICER",
        },
    )

    # 2. JSON Login
    login_res = await test_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # 3. OAuth2 Form Login (/api/v1/auth/token)
    form_res = await test_client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert form_res.status_code == 200
    form_data = form_res.json()
    assert "access_token" in form_data


@pytest.mark.asyncio
async def test_login_invalid_credentials(test_client):
    """Verify invalid password and non-existent email return 401 Unauthorized."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"valid_{unique_id}@example.com"
    password = "ValidPass123!"

    # Register
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "User",
            "organization_name": "Dept",
        },
    )

    # Wrong password
    res_wrong_pass = await test_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword999!"},
    )
    assert res_wrong_pass.status_code == 401
    assert "Invalid email or password" in res_wrong_pass.json()["detail"]

    # Non-existent user
    res_non_exist = await test_client.post(
        "/api/v1/auth/login",
        json={"email": "non_existent@example.com", "password": password},
    )
    assert res_non_exist.status_code == 401


@pytest.mark.asyncio
async def test_get_me_endpoint(test_client):
    """Verify /api/v1/auth/me returns current user profile."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"me_{unique_id}@example.com"
    password = "MePassword123!"

    # Register
    reg_res = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Profile User {unique_id}",
            "organization_name": f"Profile Dept {unique_id}",
            "role": "REVIEWER",
        },
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    # Login
    login_res = await test_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]

    # Request /me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await test_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == email.lower()
    assert me_data["role"] == "REVIEWER"
    assert me_data["organization"]["name"] == f"Profile Dept {unique_id}"


@pytest.mark.asyncio
async def test_auth_missing_or_invalid_tokens(test_client):
    """Verify missing, malformed, or fake tokens return 401."""
    # Missing token
    res_missing = await test_client.get("/api/v1/auth/me")
    assert res_missing.status_code == 401

    # Malformed token
    res_malformed = await test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert res_malformed.status_code == 401

    # Fake signed token
    fake_token = jwt.encode({"sub": str(uuid.uuid4())}, "wrong-secret-key", algorithm="HS256")
    res_fake = await test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert res_fake.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_rejected(test_client):
    """Verify deactivated user accounts cannot authenticate or access endpoints."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"inactive_{unique_id}@example.com"
    password = "InactivePass123!"

    # 1. Register active user
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "To Be Inactivated",
            "organization_name": "Test Org",
        },
    )

    # 2. Login to get token
    login_res = await test_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]

    # 3. Deactivate user directly in DB
    async with AsyncSessionLocal() as session:
        query = select(User).where(User.email == email.lower())
        res = await session.execute(query)
        db_user = res.scalar_one()
        db_user.is_active = False
        await session.commit()

    # 4. Attempt login when inactive
    login_attempt = await test_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_attempt.status_code == 403
    assert "inactive" in login_attempt.json()["detail"].lower()

    # 5. Attempt /me with previous token
    me_attempt = await test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_attempt.status_code == 403
    assert "inactive" in me_attempt.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rbac_exact_authorization_all_four_roles(test_client):
    """Verify exact role authorization across all 4 roles: ADMIN, PROCUREMENT_OFFICER, REVIEWER, AUDITOR."""
    unique_id = uuid.uuid4().hex[:8]
    tokens = {}
    roles = [
        UserRole.ADMIN,
        UserRole.PROCUREMENT_OFFICER,
        UserRole.REVIEWER,
        UserRole.AUDITOR,
    ]

    # Seed one user per role directly in DB to ensure proper role assignments
    async with AsyncSessionLocal() as session:
        org = Organization(name=f"RBAC Test Org {unique_id}")
        session.add(org)
        await session.flush()

        for role in roles:
            email = f"rbac_{role.value.lower()}_{unique_id}@example.com"
            user = User(
                email=email,
                password_hash=get_password_hash("Password123!"),
                full_name=f"{role.value} User",
                role=role,
                organization_id=org.id,
                is_active=True,
            )
            session.add(user)
        await session.commit()

    # Obtain tokens for each role
    for role in roles:
        email = f"rbac_{role.value.lower()}_{unique_id}@example.com"
        res = await test_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert res.status_code == 200
        tokens[role] = res.json()["access_token"]

    # 1. Admin-only endpoint: only ADMIN allowed (200), others 403
    res_admin = await test_client.get(
        "/api/v1/auth/test-rbac/admin-only",
        headers={"Authorization": f"Bearer {tokens[UserRole.ADMIN]}"},
    )
    assert res_admin.status_code == 200

    for forbidden_role in [UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR]:
        res_forbidden = await test_client.get(
            "/api/v1/auth/test-rbac/admin-only",
            headers={"Authorization": f"Bearer {tokens[forbidden_role]}"},
        )
        assert res_forbidden.status_code == 403, f"{forbidden_role} should be forbidden on admin-only"

    # 2. Officer-only endpoint: only PROCUREMENT_OFFICER allowed (200), others 403
    res_officer = await test_client.get(
        "/api/v1/auth/test-rbac/officer-only",
        headers={"Authorization": f"Bearer {tokens[UserRole.PROCUREMENT_OFFICER]}"},
    )
    assert res_officer.status_code == 200

    for forbidden_role in [UserRole.ADMIN, UserRole.REVIEWER, UserRole.AUDITOR]:
        res_forbidden = await test_client.get(
            "/api/v1/auth/test-rbac/officer-only",
            headers={"Authorization": f"Bearer {tokens[forbidden_role]}"},
        )
        assert res_forbidden.status_code == 403, f"{forbidden_role} should be forbidden on officer-only"

    # 3. Reviewer-only endpoint: only REVIEWER allowed (200), others 403
    res_reviewer = await test_client.get(
        "/api/v1/auth/test-rbac/reviewer-only",
        headers={"Authorization": f"Bearer {tokens[UserRole.REVIEWER]}"},
    )
    assert res_reviewer.status_code == 200

    for forbidden_role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR]:
        res_forbidden = await test_client.get(
            "/api/v1/auth/test-rbac/reviewer-only",
            headers={"Authorization": f"Bearer {tokens[forbidden_role]}"},
        )
        assert res_forbidden.status_code == 403, f"{forbidden_role} should be forbidden on reviewer-only"

    # 4. Auditor-only endpoint: only AUDITOR allowed (200), others 403
    res_auditor = await test_client.get(
        "/api/v1/auth/test-rbac/auditor-only",
        headers={"Authorization": f"Bearer {tokens[UserRole.AUDITOR]}"},
    )
    assert res_auditor.status_code == 200

    for forbidden_role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER]:
        res_forbidden = await test_client.get(
            "/api/v1/auth/test-rbac/auditor-only",
            headers={"Authorization": f"Bearer {tokens[forbidden_role]}"},
        )
        assert res_forbidden.status_code == 403, f"{forbidden_role} should be forbidden on auditor-only"

    # 5. Multi-role endpoint (Admin or Officer): both ADMIN and OFFICER allowed (200), REVIEWER & AUDITOR forbidden (403)
    res_multi_admin = await test_client.get(
        "/api/v1/auth/test-rbac/admin-or-officer",
        headers={"Authorization": f"Bearer {tokens[UserRole.ADMIN]}"},
    )
    assert res_multi_admin.status_code == 200

    res_multi_officer = await test_client.get(
        "/api/v1/auth/test-rbac/admin-or-officer",
        headers={"Authorization": f"Bearer {tokens[UserRole.PROCUREMENT_OFFICER]}"},
    )
    assert res_multi_officer.status_code == 200

    for forbidden_role in [UserRole.REVIEWER, UserRole.AUDITOR]:
        res_forbidden = await test_client.get(
            "/api/v1/auth/test-rbac/admin-or-officer",
            headers={"Authorization": f"Bearer {tokens[forbidden_role]}"},
        )
        assert res_forbidden.status_code == 403, f"{forbidden_role} should be forbidden on admin-or-officer"
