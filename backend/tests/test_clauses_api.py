import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.enums import ClauseCategory, DocumentProcessingStatus, TenderStatus, UserRole
from app.models.tender import Tender, TenderDocument, TenderPage
from app.models.clause import TenderClause
from app.models.user import Organization, User


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def setup_clause_test_env(test_client):
    """Setup test organizations, users, tenders, documents, and realistic pages."""
    uid = uuid.uuid4().hex[:8]
    org_a_name = f"Clause Org A {uid}"
    org_b_name = f"Clause Org B {uid}"

    tokens = {}
    users = {}
    orgs = {}
    tenders = {}

    async with AsyncSessionLocal() as session:
        # 1. Organizations
        org_a = Organization(name=org_a_name)
        org_b = Organization(name=org_b_name)
        session.add_all([org_a, org_b])
        await session.flush()
        orgs["A"] = org_a
        orgs["B"] = org_b

        # 2. Users
        for role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR]:
            u_a = User(
                email=f"clause_a_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("ClausePass123!"),
                full_name=f"Org A {role.value}",
                role=role,
                organization_id=org_a.id,
                is_active=True,
            )
            u_b = User(
                email=f"clause_b_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("ClausePass123!"),
                full_name=f"Org B {role.value}",
                role=role,
                organization_id=org_b.id,
                is_active=True,
            )
            session.add_all([u_a, u_b])
            users[f"A_{role.value}"] = u_a
            users[f"B_{role.value}"] = u_b

        await session.flush()

        # 3. Tenders
        deadline = datetime.now(timezone.utc) + timedelta(days=30)
        t_a = Tender(
            organization_id=org_a.id,
            tender_number=f"TND-CLAUSE-A-{uid}",
            title="Org A Pressure Vessel Tender",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["A_PROCUREMENT_OFFICER"].id,
        )
        t_b = Tender(
            organization_id=org_b.id,
            tender_number=f"TND-CLAUSE-B-{uid}",
            title="Org B Storage Tank Tender",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["B_PROCUREMENT_OFFICER"].id,
        )
        session.add_all([t_a, t_b])
        await session.flush()
        tenders["A"] = t_a
        tenders["B"] = t_b

        # 4. TenderDocument for Tender A
        doc_a = TenderDocument(
            tender_id=t_a.id,
            organization_id=org_a.id,
            filename=f"{uuid.uuid4()}.pdf",
            original_filename="Tender_Specifications_CPCL.pdf",
            storage_path="uploads/mock_spec.pdf",
            mime_type="application/pdf",
            file_size=2048,
            sha256_hash=uuid.uuid4().hex,
            page_count=2,
            processing_status=DocumentProcessingStatus.PROCESSED,
            uploaded_by=users["A_PROCUREMENT_OFFICER"].id,
        )
        session.add(doc_a)
        await session.flush()

        # 5. TenderPages with realistic tender text
        p1 = TenderPage(
            document_id=doc_a.id,
            page_number=1,
            text_content="""
            1.0 Technical Specifications
            All pressure vessel fabrication shall comply with ASME Section VIII Div 1. The GA drawing, bill of materials (BOM), and 100% NDT radiography test report must be submitted.
            
            2.0 Statutory Registrations
            Bidder must furnish valid GSTIN registration certificate and PAN copy. The establishment must comply with statutory requirements under the MSME Act.
            """,
        )
        p2 = TenderPage(
            document_id=doc_a.id,
            page_number=2,
            text_content="""
            3.0 Commercial and Payment Terms
            100% payment terms within 30 days of receipt of invoice. Delivery period shall be 6 weeks. Liquidated damages of 0.5% per week subject to penalty max 10%.
            
            4.0 Bid Validity and Administrative Terms
            The bid validity shall be strictly 120 days from opening. Any communication regarding queries must be addressed to the nodal officer.
            """,
        )
        session.add_all([p1, p2])
        await session.commit()
        await session.refresh(t_a)
        await session.refresh(t_b)

    # Login to acquire tokens
    for key, user in users.items():
        res = await test_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "ClausePass123!"},
        )
        assert res.status_code == 200, res.text
        tokens[key] = res.json()["access_token"]

    return {
        "orgs": orgs,
        "users": users,
        "tokens": tokens,
        "tenders": tenders,
    }


@pytest.mark.asyncio
async def test_extract_clauses_flow(test_client, setup_clause_test_env):
    """Test extracting clauses, listing, filtering, search, and idempotency."""
    env = setup_clause_test_env
    token_officer = env["tokens"]["A_PROCUREMENT_OFFICER"]
    tender_a_id = env["tenders"]["A"].id

    headers = {"Authorization": f"Bearer {token_officer}"}

    # 1. Trigger extraction
    res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-clauses",
        headers=headers,
        json={"force_reextract": False},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["tender_id"] == str(tender_a_id)
    assert data["total_clauses"] == 4
    breakdown = data["categories_breakdown"]
    assert "TECHNICAL" in breakdown
    assert "STATUTORY" in breakdown
    assert "COMMERCIAL" in breakdown
    assert "ADMINISTRATIVE" in breakdown

    # 2. List extracted clauses
    list_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses",
        headers=headers,
    )
    assert list_res.status_code == 200, list_res.text
    list_data = list_res.json()
    assert list_data["total"] == 4
    assert len(list_data["items"]) == 4

    first_clause = list_data["items"][0]
    assert first_clause["clause_number"] == "1.0"
    assert first_clause["title"] == "Technical Specifications"
    assert first_clause["category"] == "TECHNICAL"
    assert first_clause["page_number"] == 1
    assert first_clause["extraction_method"] == "RULE_BASED"
    assert first_clause["confidence"] > 0.70

    # 3. Filter by category
    filter_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses?category=STATUTORY",
        headers=headers,
    )
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    assert filter_data["total"] == 1
    assert filter_data["items"][0]["category"] == "STATUTORY"
    assert "GSTIN" in filter_data["items"][0]["clause_text"]

    # 4. Search text
    search_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses?search=liquidated",
        headers=headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] == 1
    assert search_data["items"][0]["category"] == "COMMERCIAL"

    # 5. Pagination
    page_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses?page=1&page_size=2",
        headers=headers,
    )
    assert page_res.status_code == 200
    page_data = page_res.json()
    assert page_data["total"] == 4
    assert len(page_data["items"]) == 2

    # 6. Retrieve single clause details
    clause_id = first_clause["id"]
    single_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses/{clause_id}",
        headers=headers,
    )
    assert single_res.status_code == 200
    single_data = single_res.json()
    assert single_data["id"] == clause_id
    assert single_data["title"] == "Technical Specifications"

    # 7. Idempotency test (repeat without force_reextract)
    repeat_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-clauses",
        headers=headers,
        json={"force_reextract": False},
    )
    assert repeat_res.status_code == 200
    assert repeat_res.json()["total_clauses"] == 4

    # Verify total DB count didn't duplicate
    verify_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses",
        headers=headers,
    )
    assert verify_res.json()["total"] == 4

    # 8. Force re-extraction
    force_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-clauses",
        headers=headers,
        json={"force_reextract": True},
    )
    assert force_res.status_code == 200
    assert force_res.json()["total_clauses"] == 4


@pytest.mark.asyncio
async def test_rbac_and_tenant_isolation(test_client, setup_clause_test_env):
    """Test role restrictions and multi-tenant isolation."""
    env = setup_clause_test_env
    tender_a_id = env["tenders"]["A"].id
    tender_b_id = env["tenders"]["B"].id

    token_a_auditor = env["tokens"]["A_AUDITOR"]
    token_b_officer = env["tokens"]["B_PROCUREMENT_OFFICER"]

    # 1. Auditor cannot trigger extraction (403 Forbidden)
    auditor_extract_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-clauses",
        headers={"Authorization": f"Bearer {token_a_auditor}"},
        json={"force_reextract": False},
    )
    assert auditor_extract_res.status_code == 403

    # 2. Extract clauses with officer first
    officer_a_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-clauses",
        headers={"Authorization": f"Bearer {env['tokens']['A_PROCUREMENT_OFFICER']}"},
        json={"force_reextract": False},
    )
    assert officer_a_res.status_code == 200

    # 3. Auditor CAN read clauses (200 OK)
    auditor_list_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses",
        headers={"Authorization": f"Bearer {token_a_auditor}"},
    )
    assert auditor_list_res.status_code == 200
    assert auditor_list_res.json()["total"] == 4

    # 4. Multi-tenant isolation: Org B officer cannot view Org A tender clauses (404 Not Found)
    cross_org_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses",
        headers={"Authorization": f"Bearer {token_b_officer}"},
    )
    assert cross_org_res.status_code == 404

    # 5. Tender with no documents returns 400 Bad Request
    no_doc_res = await test_client.post(
        f"/api/v1/tenders/{tender_b_id}/extract-clauses",
        headers={"Authorization": f"Bearer {token_b_officer}"},
        json={"force_reextract": False},
    )
    assert no_doc_res.status_code == 400
    assert "no documents" in no_doc_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_nonexistent_tender_and_clause_404(test_client, setup_clause_test_env):
    """Test 404 responses for nonexistent tender and clause IDs."""
    env = setup_clause_test_env
    token_officer = env["tokens"]["A_PROCUREMENT_OFFICER"]
    headers = {"Authorization": f"Bearer {token_officer}"}

    fake_tender_id = uuid.uuid4()
    fake_clause_id = uuid.uuid4()

    # Extract on nonexistent tender
    res = await test_client.post(
        f"/api/v1/tenders/{fake_tender_id}/extract-clauses",
        headers=headers,
    )
    assert res.status_code == 404

    # List on nonexistent tender
    res = await test_client.get(
        f"/api/v1/tenders/{fake_tender_id}/clauses",
        headers=headers,
    )
    assert res.status_code == 404

    # Single clause on valid tender but fake clause ID
    tender_a_id = env["tenders"]["A"].id
    res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/clauses/{fake_clause_id}",
        headers=headers,
    )
    assert res.status_code == 404
