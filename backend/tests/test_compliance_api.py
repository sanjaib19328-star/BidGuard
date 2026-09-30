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
    ComplianceRuleType,
    DocumentProcessingStatus,
    EvaluationStatus,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    TenderStatus,
    UserRole,
    VerificationMethod,
)
from app.models.requirement import TenderRequirement
from app.models.tender import Tender, TenderDocument, TenderPage
from app.models.user import Organization, User


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def setup_compliance_test_env(test_client):
    """Setup test organizations, users, tenders, documents, clauses, and requirements."""
    uid = uuid.uuid4().hex[:8]
    org_a_name = f"Comp Org A {uid}"
    org_b_name = f"Comp Org B {uid}"

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
                email=f"comp_a_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("CompPass123!"),
                full_name=f"Org A {role.value}",
                role=role,
                organization_id=org_a.id,
                is_active=True,
            )
            u_b = User(
                email=f"comp_b_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("CompPass123!"),
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
            tender_number=f"TND-COMP-A-{uid}",
            title="Org A Industrial Generator Procurement",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["A_PROCUREMENT_OFFICER"].id,
        )
        t_b = Tender(
            organization_id=org_b.id,
            tender_number=f"TND-COMP-B-{uid}",
            title="Org B Medical Equipment Procurement",
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
            filename="tender_spec.pdf",
            original_filename="tender_spec.pdf",
            file_size=10240,
            mime_type="application/pdf",
            sha256_hash=f"hash_comp_a_{uid}",
            storage_path=f"/dummy/path/tender_comp_a_{uid}.pdf",
            page_count=2,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )
        session.add(doc_a)
        await session.flush()

        page_a1 = TenderPage(
            document_id=doc_a.id,
            page_number=1,
            text_content="Clause 1: Eligibility. Clause 2: Financial Criteria.",
        )
        session.add(page_a1)
        await session.flush()

        # 5. Clauses for Tender A
        c1 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=page_a1.id,
            clause_number="1.1",
            category=ClauseCategory.FINANCIAL,
            title="Financial Turnover Criteria",
            clause_text="Average annual turnover of at least ₹10 crore during last 3 financial years.",
            sequence_order=1,
            page_number=1,
            confidence=0.95,
        )
        c2 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=page_a1.id,
            clause_number="2.1",
            category=ClauseCategory.STATUTORY,
            title="Statutory Registrations",
            clause_text="Bidder must submit copy of GST registration certificate.",
            sequence_order=2,
            page_number=1,
            confidence=0.92,
        )
        c3 = TenderClause(
            tender_id=t_a.id,
            document_id=doc_a.id,
            page_id=page_a1.id,
            clause_number="3.1",
            category=ClauseCategory.ELIGIBILITY,
            title="Debarment Status",
            clause_text="Bidder must not be blacklisted by any Government agency.",
            sequence_order=3,
            page_number=1,
            confidence=0.90,
        )
        session.add_all([c1, c2, c3])
        await session.flush()

        # 6. Requirements for Tender A
        req1 = TenderRequirement(
            id=uuid.uuid4(),
            tender_id=t_a.id,
            clause_id=c1.id,
            category=ClauseCategory.FINANCIAL,
            requirement_type=RequirementType.MIN_TURNOVER,
            description="Minimum annual turnover of at least 10.0 CRORE_INR",
            operator=">=",
            value_numeric=10.0,
            unit="CRORE_INR",
            currency="INR",
            period="LAST_3_FINANCIAL_YEARS",
            mandatory=True,
            applicability=RequirementApplicability.ALL_BIDDERS,
            verification_method=VerificationMethod.RULE,
            risk_hint=RiskHint.HIGH,
            sequence_order=1001,
            confidence=0.95,
            requirement_signature=f"sig1_{uid}",
        )
        req2 = TenderRequirement(
            id=uuid.uuid4(),
            tender_id=t_a.id,
            clause_id=c2.id,
            category=ClauseCategory.STATUTORY,
            requirement_type=RequirementType.GST_REGISTRATION,
            description="Mandatory submission of GST registration certificate",
            operator="REQUIRED",
            required_evidence=["GST_CERTIFICATE"],
            mandatory=True,
            applicability=RequirementApplicability.ALL_BIDDERS,
            verification_method=VerificationMethod.DOCUMENT,
            risk_hint=RiskHint.HIGH,
            sequence_order=2001,
            confidence=0.92,
            requirement_signature=f"sig2_{uid}",
        )
        req3 = TenderRequirement(
            id=uuid.uuid4(),
            tender_id=t_a.id,
            clause_id=c3.id,
            category=ClauseCategory.ELIGIBILITY,
            requirement_type=RequirementType.DECLARATION_REQUIRED,
            description="Bidder must submit non-blacklisting declaration",
            operator="REQUIRED",
            mandatory=True,
            applicability=RequirementApplicability.ALL_BIDDERS,
            verification_method=VerificationMethod.DOCUMENT,
            risk_hint=RiskHint.CRITICAL,
            sequence_order=3001,
            confidence=0.90,
            requirement_signature=f"sig3_{uid}",
        )
        session.add_all([req1, req2, req3])
        await session.commit()

    # Obtain JWT tokens for each user
    for key, user in users.items():
        resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "CompPass123!"},
        )
        assert resp.status_code == 200, f"Login failed for {user.email}: {resp.text}"
        tokens[key] = resp.json()["access_token"]

    return {
        "tokens": tokens,
        "tenders": tenders,
        "orgs": orgs,
        "users": users,
    }


@pytest.mark.asyncio
async def test_compliance_rules_and_evaluation_flow(test_client, setup_compliance_test_env):
    """End-to-end test: compile rules, list rules, evaluate against evidence, safe re-compilation."""
    env = setup_compliance_test_env
    token_officer_a = env["tokens"]["A_PROCUREMENT_OFFICER"]
    tender_a_id = str(env["tenders"]["A"].id)
    headers_officer = {"Authorization": f"Bearer {token_officer_a}"}

    # 1. Compile Rules
    compile_resp = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/compile-rules",
        headers=headers_officer,
        json={"force_recompile": False},
    )
    assert compile_resp.status_code == 200
    comp_data = compile_resp.json()
    assert comp_data["tender_id"] == tender_a_id
    assert comp_data["rules_total"] == 3
    assert comp_data["rules_created"] == 3
    assert comp_data["rules_reused"] == 0
    assert "NUMERIC_THRESHOLD" in comp_data["rules_by_type"]

    # 2. List Rules
    list_resp = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/rules",
        headers=headers_officer,
    )
    assert list_resp.status_code == 200
    rules_data = list_resp.json()
    assert rules_data["total"] == 3
    assert len(rules_data["items"]) == 3

    first_rule = rules_data["items"][0]
    rule_id = first_rule["id"]
    assert first_rule["source_requirement"] is not None
    assert first_rule["source_requirement"]["clause_number"] is not None

    # 3. Get Single Rule
    get_rule_resp = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/rules/{rule_id}",
        headers=headers_officer,
    )
    assert get_rule_resp.status_code == 200
    rule_detail = get_rule_resp.json()
    assert rule_detail["id"] == rule_id

    # 4. Evaluate Rules - Satisfying Evidence (PASS)
    evidence_pass = {
        "bidder_profile": {
            "bidder_type": "MANUFACTURER",
            "is_msme": False,
        },
        "financial": {
            "annual_turnover": {
                "value": 12.0,
                "unit": "CRORE_INR",
            }
        },
        "documents": [
            "GST_CERTIFICATE",
            "PAN_CARD",
        ],
        "declarations": {
            "non_blacklisted": True,
        },
    }

    eval_resp = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/evaluate-rules",
        headers=headers_officer,
        json={"bidder_id": "BIDDER-ALPHA", "evidence": evidence_pass},
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["tender_id"] == tender_a_id
    assert eval_data["bidder_id"] == "BIDDER-ALPHA"
    assert eval_data["summary"]["total"] == 3
    assert eval_data["summary"]["passed"] == 3
    assert eval_data["summary"]["failed"] == 0
    run_id_1 = eval_data["evaluation_run_id"]

    # 5. List Evaluations
    list_eval_resp = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/evaluations",
        headers=headers_officer,
    )
    assert list_eval_resp.status_code == 200
    evals_list = list_eval_resp.json()
    assert evals_list["summary"]["total"] == 3
    assert evals_list["summary"]["passed"] == 3

    # 6. Evaluate Rules - Deficient Evidence (FAIL & NOT_VERIFIABLE)
    evidence_fail = {
        "bidder_profile": {
            "bidder_type": "MANUFACTURER",
        },
        "financial": {
            "annual_turnover": {
                "value": 4.0,  # Below 10.0 Cr -> FAIL
                "unit": "CRORE_INR",
            }
        },
        "documents": [],  # GST certificate missing from provided list -> FAIL
        # declarations missing -> NOT_VERIFIABLE
    }

    eval_fail_resp = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/evaluate-rules",
        headers=headers_officer,
        json={"bidder_id": "BIDDER-BETA", "evidence": evidence_fail},
    )
    assert eval_fail_resp.status_code == 200
    eval_fail_data = eval_fail_resp.json()
    assert eval_fail_data["summary"]["failed"] == 2  # turnover and GST
    assert eval_fail_data["summary"]["not_verifiable"] == 1  # missing declaration

    # 7. Safe Re-compilation:
    # Idempotent re-run with force_recompile=False reuses existing rules
    compile_reused = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/compile-rules",
        headers=headers_officer,
        json={"force_recompile": False},
    )
    assert compile_reused.status_code == 200
    assert compile_reused.json()["rules_reused"] == 3

    # Force re-compilation with force_recompile=True updates in-place and preserves evaluations
    compile_forced = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/compile-rules",
        headers=headers_officer,
        json={"force_recompile": True},
    )
    assert compile_forced.status_code == 200
    assert compile_forced.json()["rules_updated"] == 3

    # Confirm historical evaluations still exist for both run 1 and run 2 (6 total)
    hist_eval_resp = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/evaluations",
        headers=headers_officer,
    )
    assert hist_eval_resp.status_code == 200
    assert hist_eval_resp.json()["summary"]["total"] == 6


@pytest.mark.asyncio
async def test_compliance_rbac_and_tenant_isolation(test_client, setup_compliance_test_env):
    """Verify tenant isolation and RBAC constraints for compliance APIs."""
    env = setup_compliance_test_env
    tender_a_id = str(env["tenders"]["A"].id)

    token_officer_b = env["tokens"]["B_PROCUREMENT_OFFICER"]
    headers_org_b = {"Authorization": f"Bearer {token_officer_b}"}

    # Org B officer cannot compile rules for Org A tender -> 404
    resp = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/compile-rules",
        headers=headers_org_b,
        json={"force_recompile": False},
    )
    assert resp.status_code == 404

    # Org B officer cannot view Org A rules -> 404
    resp = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/rules",
        headers=headers_org_b,
    )
    assert resp.status_code == 404

    # Org B officer cannot evaluate Org A rules -> 404
    resp = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/evaluate-rules",
        headers=headers_org_b,
        json={"evidence": {}},
    )
    assert resp.status_code == 404

    # Unauthenticated calls rejected -> 401
    resp = await test_client.post(f"/api/v1/tenders/{tender_a_id}/compile-rules")
    assert resp.status_code == 401

    resp = await test_client.get(f"/api/v1/tenders/{tender_a_id}/rules")
    assert resp.status_code == 401
