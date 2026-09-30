import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.clause import TenderClause
from app.models.enums import (
    ClauseCategory,
    DocumentProcessingStatus,
    RequirementType,
    TenderStatus,
    UserRole,
)
from app.models.requirement import TenderRequirement
from app.models.tender import Tender, TenderDocument, TenderPage
from app.models.user import Organization, User


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def setup_requirements_test_env(test_client):
    """Setup test organizations, users, tenders, documents, and realistic clauses."""
    uid = uuid.uuid4().hex[:8]
    org_a_name = f"Req Org A {uid}"
    org_b_name = f"Req Org B {uid}"

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
                email=f"req_a_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("ReqPass123!"),
                full_name=f"Org A {role.value}",
                role=role,
                organization_id=org_a.id,
                is_active=True,
            )
            u_b = User(
                email=f"req_b_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("ReqPass123!"),
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
            tender_number=f"TND-REQ-A-{uid}",
            title="Org A Equipment Procurement",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["A_PROCUREMENT_OFFICER"].id,
        )
        t_b = Tender(
            organization_id=org_b.id,
            tender_number=f"TND-REQ-B-{uid}",
            title="Org B Storage Tank Procurement",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["B_PROCUREMENT_OFFICER"].id,
        )
        session.add_all([t_a, t_b])
        await session.flush()
        tenders["A"] = t_a
        tenders["B"] = t_b

        # 4. TenderDocument & TenderPage for Tender A
        doc_a = TenderDocument(
            tender_id=t_a.id,
            organization_id=org_a.id,
            filename=f"{uuid.uuid4()}.pdf",
            original_filename="Tender_Doc_A.pdf",
            storage_path="uploads/mock_req.pdf",
            mime_type="application/pdf",
            file_size=2048,
            sha256_hash=uuid.uuid4().hex,
            page_count=2,
            processing_status=DocumentProcessingStatus.PROCESSED,
            uploaded_by=users["A_PROCUREMENT_OFFICER"].id,
        )
        session.add(doc_a)
        await session.flush()

        p1 = TenderPage(
            document_id=doc_a.id,
            page_number=1,
            text_content="Page 1 text",
        )
        p2 = TenderPage(
            document_id=doc_a.id,
            page_number=2,
            text_content="Page 2 text",
        )
        session.add_all([p1, p2])
        await session.flush()

        # 5. TenderClauses for Tender A
        c1 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=p1.id,
            page_number=1,
            clause_number="1.0",
            title="Annual Turnover Requirement",
            clause_text="The bidder shall have an average annual turnover of at least ₹10 crore during the last three financial years.",
            category=ClauseCategory.FINANCIAL,
            sequence_order=1,
            extraction_method="RULE_BASED",
            confidence=0.95,
        )
        c2 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=p1.id,
            page_number=1,
            clause_number="2.0",
            title="Statutory Registrations",
            clause_text="Bidder must furnish valid GSTIN registration certificate and PAN copy.",
            category=ClauseCategory.STATUTORY,
            sequence_order=2,
            extraction_method="RULE_BASED",
            confidence=0.92,
        )
        c3 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=p2.id,
            page_number=2,
            clause_number="3.0",
            title="Technical Pressure Vessel Specifications",
            clause_text="All fabrication must comply with ASME Section VIII Div 1. Radiography NDT report is required.",
            category=ClauseCategory.TECHNICAL,
            sequence_order=3,
            extraction_method="RULE_BASED",
            confidence=0.90,
        )
        c4 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=p2.id,
            page_number=2,
            clause_number="4.0",
            title="Delivery Schedule",
            clause_text="Delivery shall be completed within 60 days from order date.",
            category=ClauseCategory.COMMERCIAL,
            sequence_order=4,
            extraction_method="RULE_BASED",
            confidence=0.88,
        )
        c5 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=p2.id,
            page_number=2,
            clause_number="5.0",
            title="General Information",
            clause_text="This tender was published on the portal. Bidders are advised to visit the website regularly.",
            category=ClauseCategory.GENERAL,
            sequence_order=5,
            extraction_method="RULE_BASED",
            confidence=0.50,
        )
        session.add_all([c1, c2, c3, c4, c5])
        await session.commit()
        await session.refresh(t_a)
        await session.refresh(t_b)

    # Login to acquire tokens
    for key, user in users.items():
        res = await test_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "ReqPass123!"},
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
async def test_extract_and_list_requirements_flow(test_client, setup_requirements_test_env):
    """Test full requirements extraction flow, filtering, search, pagination, and idempotency."""
    env = setup_requirements_test_env
    token_officer = env["tokens"]["A_PROCUREMENT_OFFICER"]
    tender_a_id = env["tenders"]["A"].id

    headers = {"Authorization": f"Bearer {token_officer}"}

    # 1. Trigger extraction
    res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-requirements",
        headers=headers,
        json={"force_reextract": False},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["tender_id"] == str(tender_a_id)
    assert data["requirements_created"] >= 4
    assert data["requirements_reused"] == 0
    assert data["status"] == "COMPLETED"
    cat_breakdown = data["categories_breakdown"]
    assert "FINANCIAL" in cat_breakdown
    assert "STATUTORY" in cat_breakdown
    assert "TECHNICAL" in cat_breakdown
    assert "COMMERCIAL" in cat_breakdown

    # 2. List requirements
    list_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements",
        headers=headers,
    )
    assert list_res.status_code == 200, list_res.text
    list_data = list_res.json()
    assert list_data["total"] >= 4
    items = list_data["items"]

    # Verify source traceability
    first_req = items[0]
    assert first_req["source"] is not None
    assert first_req["source"]["clause_id"] is not None
    assert first_req["source"]["page_number"] in (1, 2)
    assert first_req["source"]["document_id"] is not None

    # 3. Filter by category
    fin_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements?category=FINANCIAL",
        headers=headers,
    )
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["total"] == 1
    req_fin = fin_data["items"][0]
    assert req_fin["requirement_type"] == "MIN_TURNOVER"
    assert req_fin["operator"] == ">="
    assert req_fin["value_numeric"] == 10.0
    assert req_fin["unit"] == "CRORE_INR"
    assert req_fin["currency"] == "INR"
    assert req_fin["period"] == "LAST_3_FINANCIAL_YEARS"
    assert req_fin["mandatory"] is True
    assert req_fin["applicability"] == "ALL_BIDDERS"
    assert "FINANCIAL_STATEMENTS" in req_fin["required_evidence"]
    assert req_fin["verification_method"] == "DOCUMENT"
    assert req_fin["risk_hint"] == "HIGH"

    # 4. Search text
    search_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements?search=ASME",
        headers=headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] == 1
    assert "ASME" in search_data["items"][0]["description"]

    # 5. Pagination
    page_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements?page=1&page_size=2",
        headers=headers,
    )
    assert page_res.status_code == 200
    page_data = page_res.json()
    assert len(page_data["items"]) == 2
    assert page_data["total"] >= 4

    # 6. Retrieve single requirement
    req_id = first_req["id"]
    single_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements/{req_id}",
        headers=headers,
    )
    assert single_res.status_code == 200
    single_data = single_res.json()
    assert single_data["id"] == req_id
    assert single_data["source"]["clause_id"] is not None

    # 7. Idempotency test (rerun with force_reextract=False)
    repeat_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-requirements",
        headers=headers,
        json={"force_reextract": False},
    )
    assert repeat_res.status_code == 200
    repeat_data = repeat_res.json()
    assert repeat_data["requirements_created"] == 0
    assert repeat_data["requirements_reused"] == data["requirements_total"]

    # 8. Force re-extraction
    force_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-requirements",
        headers=headers,
        json={"force_reextract": True},
    )
    assert force_res.status_code == 200
    force_data = force_res.json()
    assert force_data["requirements_created"] >= 4
    assert force_data["requirements_reused"] == 0


@pytest.mark.asyncio
async def test_requirements_rbac_and_tenant_isolation(test_client, setup_requirements_test_env):
    """Verify role authorization limits and strict multi-tenant isolation."""
    env = setup_requirements_test_env
    tender_a_id = env["tenders"]["A"].id
    tender_b_id = env["tenders"]["B"].id

    token_a_auditor = env["tokens"]["A_AUDITOR"]
    token_a_officer = env["tokens"]["A_PROCUREMENT_OFFICER"]
    token_b_officer = env["tokens"]["B_PROCUREMENT_OFFICER"]

    # 1. Auditor cannot trigger extraction (403 Forbidden)
    auditor_extract_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-requirements",
        headers={"Authorization": f"Bearer {token_a_auditor}"},
        json={"force_reextract": False},
    )
    assert auditor_extract_res.status_code == 403

    # 2. Extract with officer first
    officer_a_res = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/extract-requirements",
        headers={"Authorization": f"Bearer {token_a_officer}"},
        json={"force_reextract": False},
    )
    assert officer_a_res.status_code == 200

    # 3. Auditor CAN view requirements (200 OK)
    auditor_list_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements",
        headers={"Authorization": f"Bearer {token_a_auditor}"},
    )
    assert auditor_list_res.status_code == 200
    assert auditor_list_res.json()["total"] >= 4

    # 4. Multi-tenant isolation: Org B officer cannot view Org A requirements (404 Not Found)
    cross_org_res = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/requirements",
        headers={"Authorization": f"Bearer {token_b_officer}"},
    )
    assert cross_org_res.status_code == 404

    # 5. Tender with no clauses returns 400 Bad Request
    no_clauses_res = await test_client.post(
        f"/api/v1/tenders/{tender_b_id}/extract-requirements",
        headers={"Authorization": f"Bearer {token_b_officer}"},
        json={"force_reextract": False},
    )
    assert no_clauses_res.status_code == 400
    assert "no extracted clauses" in no_clauses_res.json()["detail"].lower()

    # 6. Nonexistent tender returns 404
    fake_id = uuid.uuid4()
    not_found_res = await test_client.post(
        f"/api/v1/tenders/{fake_id}/extract-requirements",
        headers={"Authorization": f"Bearer {token_a_officer}"},
    )
    assert not_found_res.status_code == 404
