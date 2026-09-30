import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Dict, Any
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.audit import AuditLog
from app.models.enums import TenderStatus, UserRole
from app.models.tender import Tender
from app.models.user import Organization, User


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def create_user_helper(email: str, role: UserRole, org_name: str, password: str = "Password123!") -> Tuple[User, str]:
    """Helper to create an organization and user, then return user entity and login JWT token."""
    pass


@pytest.fixture
async def setup_orgs_and_users(test_client):
    """Setup test organizations and users with all 4 roles."""
    uid = uuid.uuid4().hex[:8]
    org_a_name = f"Org A {uid}"
    org_b_name = f"Org B {uid}"

    tokens = {}
    users = {}
    orgs = {}

    async with AsyncSessionLocal() as session:
        # Org A
        org_a = Organization(name=org_a_name)
        session.add(org_a)
        await session.flush()
        orgs["A"] = org_a

        # Org B
        org_b = Organization(name=org_b_name)
        session.add(org_b)
        await session.flush()
        orgs["B"] = org_b

        # Users for Org A
        for role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR]:
            email = f"user_a_{role.value.lower()}_{uid}@example.com"
            user = User(
                email=email,
                password_hash=get_password_hash("Password123!"),
                full_name=f"Org A {role.value}",
                role=role,
                organization_id=org_a.id,
                is_active=True,
            )
            session.add(user)
            users[f"A_{role.value}"] = user

        # Users for Org B
        for role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR]:
            email = f"user_b_{role.value.lower()}_{uid}@example.com"
            user = User(
                email=email,
                password_hash=get_password_hash("Password123!"),
                full_name=f"Org B {role.value}",
                role=role,
                organization_id=org_b.id,
                is_active=True,
            )
            session.add(user)
            users[f"B_{role.value}"] = user

        await session.commit()

    # Login and get tokens
    for key, user in users.items():
        res = await test_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "Password123!"},
        )
        assert res.status_code == 200, res.text
        tokens[key] = res.json()["access_token"]

    return {
        "orgs": orgs,
        "users": users,
        "tokens": tokens,
    }


# ==============================================================================
# 1. Authentication Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_unauthenticated_requests_fail(test_client):
    """Verify all tender endpoints require valid JWT authentication (401)."""
    fake_id = uuid.uuid4()
    
    res = await test_client.post("/api/v1/tenders", json={"title": "Test"})
    assert res.status_code == 401

    res = await test_client.get("/api/v1/tenders")
    assert res.status_code == 401

    res = await test_client.get(f"/api/v1/tenders/{fake_id}")
    assert res.status_code == 401

    res = await test_client.patch(f"/api/v1/tenders/{fake_id}", json={"title": "Updated"})
    assert res.status_code == 401

    res = await test_client.post(f"/api/v1/tenders/{fake_id}/status", json={"status": "READY"})
    assert res.status_code == 401

    res = await test_client.post(f"/api/v1/tenders/{fake_id}/archive")
    assert res.status_code == 401

    res = await test_client.delete(f"/api/v1/tenders/{fake_id}")
    assert res.status_code == 401


# ==============================================================================
# 2. Creation & Role Authorization Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_tender_creation_roles(test_client, setup_orgs_and_users):
    """Verify ADMIN and PROCUREMENT_OFFICER can create tenders; REVIEWER and AUDITOR get 403."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # 1. Procurement Officer -> Success (201)
    payload_po = {
        "tender_number": f"GEM/2026/PO/{uuid.uuid4().hex[:6]}",
        "title": "Procurement of Server Racks",
        "description": "High quality server racks for GeM data center",
        "procuring_entity": "National Informatics Centre",
        "department": "Electronics & IT",
        "category": "Goods",
        "tender_type": "Open",
        "source_portal": "GeM",
        "source_url": "https://gem.gov.in/tenders/12345",
        "submission_deadline": deadline,
    }
    res_po = await test_client.post(
        "/api/v1/tenders",
        json=payload_po,
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_po.status_code == 201, res_po.text
    data_po = res_po.json()
    assert data_po["title"] == payload_po["title"]
    assert data_po["status"] == "DRAFT"
    assert data_po["organization_id"] == str(setup_orgs_and_users["orgs"]["A"].id)

    # 2. Admin -> Success (201)
    payload_admin = {
        "tender_number": f"GEM/2026/ADM/{uuid.uuid4().hex[:6]}",
        "title": "Laptops for Defence Department",
        "submission_deadline": deadline,
    }
    res_admin = await test_client.post(
        "/api/v1/tenders",
        json=payload_admin,
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_admin.status_code == 201

    # 3. Reviewer -> Forbidden (403)
    res_rev = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"GEM/2026/REV/{uuid.uuid4().hex[:6]}", "title": "Test", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_rev.status_code == 403

    # 4. Auditor -> Forbidden (403)
    res_aud = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"GEM/2026/AUD/{uuid.uuid4().hex[:6]}", "title": "Test", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_aud.status_code == 403


# ==============================================================================
# 3. Organization Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_organization_isolation(test_client, setup_orgs_and_users):
    """Verify Org A cannot access, view, modify, or delete Org B tenders (returns 404)."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()

    # Create tender in Org B
    res_b = await test_client.post(
        "/api/v1/tenders",
        json={
            "tender_number": f"GEM/B/{uuid.uuid4().hex[:6]}",
            "title": "Confidential Ministry of Home Affairs Tender",
            "procuring_entity": "MHA",
            "submission_deadline": deadline,
        },
        headers={"Authorization": f"Bearer {tokens['B_PROCUREMENT_OFFICER']}"},
    )
    assert res_b.status_code == 201
    tender_b_id = res_b.json()["id"]

    # Org A user attempts GET /tenders/{tender_b_id} -> 404 Not Found
    res_get_a = await test_client.get(
        f"/api/v1/tenders/{tender_b_id}",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_get_a.status_code == 404

    # Org A user attempts PATCH -> 404 Not Found
    res_patch_a = await test_client.patch(
        f"/api/v1/tenders/{tender_b_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_patch_a.status_code == 404

    # Org A user attempts DELETE -> 404 Not Found
    res_del_a = await test_client.delete(
        f"/api/v1/tenders/{tender_b_id}",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_del_a.status_code == 404

    # Org A user listing tenders does NOT include Org B tender
    res_list_a = await test_client.get(
        "/api/v1/tenders",
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_list_a.status_code == 200
    item_ids = [item["id"] for item in res_list_a.json()["items"]]
    assert tender_b_id not in item_ids


# ==============================================================================
# 4. Duplicate Tender Number Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_duplicate_tender_number_rules(test_client, setup_orgs_and_users):
    """Verify tender_number is unique per organization, but can be shared across organizations."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    same_tender_num = f"TENDER-SHARED-{uuid.uuid4().hex[:6]}"

    # Org A creates tender with same_tender_num
    res_a = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": same_tender_num, "title": "Org A Tender", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_a.status_code == 201

    # Org A creates duplicate tender with same_tender_num -> 409 Conflict
    res_a_dup = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": same_tender_num, "title": "Org A Duplicate", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_a_dup.status_code == 409

    # Org B creates tender with same_tender_num -> 201 Success
    res_b = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": same_tender_num, "title": "Org B Tender", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['B_PROCUREMENT_OFFICER']}"},
    )
    assert res_b.status_code == 201


# ==============================================================================
# 5. Search, Filter, and Pagination Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_search_filter_and_pagination(test_client, setup_orgs_and_users):
    """Verify search across title, tender_number, and procuring_entity, status filtering, and pagination."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
    unique_keyword = f"Keyword{uuid.uuid4().hex[:6]}"

    # Create 3 distinct tenders in Org A
    await test_client.post(
        "/api/v1/tenders",
        json={
            "tender_number": f"NUM-1-{unique_keyword}",
            "title": f"Special {unique_keyword} Project",
            "procuring_entity": "Indian Space Research Organisation",
            "submission_deadline": deadline,
        },
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    await test_client.post(
        "/api/v1/tenders",
        json={
            "tender_number": f"NUM-2-{uuid.uuid4().hex[:6]}",
            "title": "Medical Equipment Procurement",
            "procuring_entity": f"Hospital {unique_keyword}",
            "submission_deadline": deadline,
        },
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )

    # Search by unique_keyword
    res_search = await test_client.get(
        f"/api/v1/tenders?search={unique_keyword}",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] >= 2
    assert all(unique_keyword.lower() in (item["title"] + item["tender_number"] + (item["procuring_entity"] or "")).lower() for item in search_data["items"])

    # Pagination test (page_size=1)
    res_page = await test_client.get(
        f"/api/v1/tenders?search={unique_keyword}&page=1&page_size=1",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_page.status_code == 200
    page_data = res_page.json()
    assert len(page_data["items"]) == 1
    assert page_data["page"] == 1
    assert page_data["page_size"] == 1


# ==============================================================================
# 6. Update Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_update_tender_roles_and_validation(test_client, setup_orgs_and_users):
    """Verify ADMIN and PROCUREMENT_OFFICER can update metadata; REVIEWER and AUDITOR cannot."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=40)).isoformat()

    # Create tender
    create_res = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"UPD-{uuid.uuid4().hex[:6]}", "title": "Initial Title", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    tender_id = create_res.json()["id"]

    # 1. Procurement Officer Update -> 200 OK
    res_upd_po = await test_client.patch(
        f"/api/v1/tenders/{tender_id}",
        json={"title": "Updated Title by PO", "description": "New description"},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_upd_po.status_code == 200
    assert res_upd_po.json()["title"] == "Updated Title by PO"

    # 2. Admin Update -> 200 OK
    res_upd_admin = await test_client.patch(
        f"/api/v1/tenders/{tender_id}",
        json={"department": "Defence R&D"},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_upd_admin.status_code == 200
    assert res_upd_admin.json()["department"] == "Defence R&D"

    # 3. Reviewer Update -> 403 Forbidden
    res_upd_rev = await test_client.patch(
        f"/api/v1/tenders/{tender_id}",
        json={"title": "Hacked by Reviewer"},
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_upd_rev.status_code == 403

    # 4. Auditor Update -> 403 Forbidden
    res_upd_aud = await test_client.patch(
        f"/api/v1/tenders/{tender_id}",
        json={"title": "Hacked by Auditor"},
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_upd_aud.status_code == 403


# ==============================================================================
# 7. Status Transition Lifecycle Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_status_transitions_and_roles(test_client, setup_orgs_and_users):
    """Verify valid status progression, invalid transitions (400), and role enforcement."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Create tender (initial DRAFT)
    res = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"STAT-{uuid.uuid4().hex[:6]}", "title": "Lifecycle Tender", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    tender_id = res.json()["id"]

    # 1. Invalid jump DRAFT -> COMPLETED -> 400 Bad Request
    res_bad = await test_client.post(
        f"/api/v1/tenders/{tender_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_bad.status_code == 400
    assert "Invalid status transition" in res_bad.json()["detail"]

    # 2. Valid transition DRAFT -> READY -> 200 OK (by PO)
    res_ready = await test_client.post(
        f"/api/v1/tenders/{tender_id}/status",
        json={"status": "READY"},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "READY"

    # 3. Valid transition READY -> UNDER_REVIEW -> 200 OK (by Reviewer)
    res_review = await test_client.post(
        f"/api/v1/tenders/{tender_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "UNDER_REVIEW"

    # 4. Auditor attempt to change status -> 403 Forbidden
    res_aud = await test_client.post(
        f"/api/v1/tenders/{tender_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_aud.status_code == 403

    # 5. Valid transition UNDER_REVIEW -> COMPLETED -> 200 OK (by Admin)
    res_comp = await test_client.post(
        f"/api/v1/tenders/{tender_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "COMPLETED"


# ==============================================================================
# 8. Archive Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_archive_tender(test_client, setup_orgs_and_users):
    """Verify archive endpoint, role authorization, and duplicate archive rejection."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Create tender
    res = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"ARC-{uuid.uuid4().hex[:6]}", "title": "To Archive", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    tender_id = res.json()["id"]

    # Reviewer attempt to archive -> 403
    res_rev = await test_client.post(
        f"/api/v1/tenders/{tender_id}/archive",
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_rev.status_code == 403

    # Procurement Officer archives -> 200 OK
    res_arc = await test_client.post(
        f"/api/v1/tenders/{tender_id}/archive",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_arc.status_code == 200
    assert res_arc.json()["status"] == "ARCHIVED"

    # Repeated archive call -> 400 Bad Request
    res_dup_arc = await test_client.post(
        f"/api/v1/tenders/{tender_id}/archive",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_dup_arc.status_code == 400
    assert "already archived" in res_dup_arc.json()["detail"].lower()


# ==============================================================================
# 9. Delete Constraints Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_delete_tender_rules(test_client, setup_orgs_and_users):
    """Verify only ADMIN can delete, and only in DRAFT status (409 Conflict if active/completed)."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # 1. Create DRAFT tender
    res_draft = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"DEL-DRAFT-{uuid.uuid4().hex[:6]}", "title": "Draft to delete", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    draft_id = res_draft.json()["id"]

    # PO attempt delete -> 403 Forbidden
    res_del_po = await test_client.delete(
        f"/api/v1/tenders/{draft_id}",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_del_po.status_code == 403

    # Admin delete DRAFT -> 204 No Content
    res_del_admin = await test_client.delete(
        f"/api/v1/tenders/{draft_id}",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_del_admin.status_code == 204

    # Verify tender is deleted
    res_get_deleted = await test_client.get(
        f"/api/v1/tenders/{draft_id}",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_get_deleted.status_code == 404

    # 2. Create tender and move to READY
    res_ready = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"DEL-READY-{uuid.uuid4().hex[:6]}", "title": "Ready tender", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    ready_id = res_ready.json()["id"]
    await test_client.post(
        f"/api/v1/tenders/{ready_id}/status",
        json={"status": "READY"},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )

    # Admin attempt delete non-DRAFT -> 409 Conflict
    res_del_conflict = await test_client.delete(
        f"/api/v1/tenders/{ready_id}",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_del_conflict.status_code == 409
    assert "DRAFT" in res_del_conflict.json()["detail"]


# ==============================================================================
# 10. Audit Log Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_audit_logs_recorded(test_client, setup_orgs_and_users):
    """Verify TENDER_CREATED, TENDER_UPDATED, TENDER_STATUS_CHANGED, TENDER_ARCHIVED, and TENDER_DELETED audit records."""
    tokens = setup_orgs_and_users["tokens"]
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # 1. Create
    res = await test_client.post(
        "/api/v1/tenders",
        json={"tender_number": f"AUDIT-{uuid.uuid4().hex[:6]}", "title": "Audit Test", "submission_deadline": deadline},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    tender_id = res.json()["id"]

    # 2. Update
    await test_client.patch(
        f"/api/v1/tenders/{tender_id}",
        json={"title": "Audit Test Modified"},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )

    # 3. Status change
    await test_client.post(
        f"/api/v1/tenders/{tender_id}/status",
        json={"status": "READY"},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )

    # 4. Archive
    await test_client.post(
        f"/api/v1/tenders/{tender_id}/archive",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )

    # Check AuditLog records in PostgreSQL
    async with AsyncSessionLocal() as session:
        query = (
            select(AuditLog)
            .where(AuditLog.entity_id == tender_id)
            .order_by(AuditLog.created_at.asc())
        )
        res_audit = await session.execute(query)
        logs = list(res_audit.scalars().all())
        actions = [l.action for l in logs]

        assert "TENDER_CREATED" in actions
        assert "TENDER_UPDATED" in actions
        assert "TENDER_STATUS_CHANGED" in actions
        assert "TENDER_ARCHIVED" in actions

        # Verify audit details
        created_log = next(l for l in logs if l.action == "TENDER_CREATED")
        assert created_log.actor_user_id == setup_orgs_and_users["users"]["A_PROCUREMENT_OFFICER"].id
        assert created_log.new_state["tender_number"].startswith("AUDIT-")
