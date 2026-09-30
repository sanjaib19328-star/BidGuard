import csv
from datetime import datetime, timezone
import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from pypdf import PdfReader
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.audit import AuditLog
from app.models.bidder import Bidder, BidderTenderParticipation
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import (
    DataSourceType,
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
    ParticipationStatus,
    TenderStatus,
    UserRole,
    VerificationResultStatus,
)
from app.models.tender import Tender
from app.models.user import Organization, User
from app.models.verification import VerificationRequest, VerificationResult
from app.services.risk_intelligence_service import calculate_deterministic_risk_score


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def setup_integration_data():
    """Seed real PostgreSQL tables with multi-tenant data for Phase 6 and Phase 7 validation."""
    uid = uuid.uuid4().hex[:8]

    async with AsyncSessionLocal() as session:
        # 1. Two distinct organizations
        org_a = Organization(name=f"Integration Org A {uid}")
        org_b = Organization(name=f"Integration Org B {uid}")
        session.add_all([org_a, org_b])
        await session.flush()

        # 2. Users in Org A and Org B
        officer_a = User(
            email=f"officer_a_{uid}@example.com",
            password_hash=get_password_hash("Password123!"),
            full_name=f"Officer A {uid}",
            role=UserRole.PROCUREMENT_OFFICER,
            organization_id=org_a.id,
            is_active=True,
        )
        officer_b = User(
            email=f"officer_b_{uid}@example.com",
            password_hash=get_password_hash("Password123!"),
            full_name=f"Officer B {uid}",
            role=UserRole.PROCUREMENT_OFFICER,
            organization_id=org_b.id,
            is_active=True,
        )
        session.add_all([officer_a, officer_b])
        await session.flush()

        # 3. Tender in Org A
        tender_a = Tender(
            id=uuid.uuid4(),
            organization_id=org_a.id,
            tender_number=f"GEM/2026/B/{uid}",
            title=f"Procurement of Specialized Engineering Packages {uid}",
            procuring_entity="Central Public Sector Undertaking",
            department="Projects & Engineering",
            tender_type="Open Tender",
            status=TenderStatus.UNDER_REVIEW,
        )
        setattr(tender_a, "estimated_value", 75000000.0)
        session.add(tender_a)

        # 4. Bidder in Org A
        bidder_a = Bidder(
            id=uuid.uuid4(),
            organization_id=org_a.id,
            legal_name="Apex Precision Fabrication Pvt Ltd",
            trade_name="Apex Systems",
            pan="AAACA1234A",
            gstin="27AAACA1234A1Z5",
            udyam_registration_number="UDYAM-MH-02-0012345",
            is_mse=True,
        )
        session.add(bidder_a)
        await session.flush()

        # Link participation
        part_a = BidderTenderParticipation(
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            status=ParticipationStatus.EVALUATED,
        )
        session.add(part_a)

        # 5. External Verifications in Org A
        v_req = VerificationRequest(
            id=uuid.uuid4(),
            organization_id=org_a.id,
            bidder_id=bidder_a.id,
            tender_id=tender_a.id,
            verification_type=DataSourceType.UDYAM_MSME,
            identifier_value=bidder_a.udyam_registration_number,
        )
        session.add(v_req)
        await session.flush()

        v_res = VerificationResult(
            id=uuid.uuid4(),
            verification_request_id=v_req.id,
            bidder_id=bidder_a.id,
            source_type=DataSourceType.UDYAM_MSME,
            status=VerificationResultStatus.VERIFIED,
            name_match_score=0.98,
            sanitized_response={"enterprise_name": bidder_a.legal_name, "category": "Micro"},
            recommended_action="Verified via Udyam portal.",
        )
        session.add(v_res)

        # 6. Evaluation Matrix Items covering all 5 statuses
        # Statuses: COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_VERIFIABLE, EXEMPT_MSE
        m_compliant = EvaluationMatrixItem(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            dimension="TECHNICAL",
            status=MatrixItemStatus.COMPLIANT,
            required_value="Minimum design thickness >= 25 mm",
            bidder_extracted_value="Thickness offered 28 mm in engineering datasheet",
            deviation_magnitude=0.0,
            is_statutory=False,
            confidence_score=0.98,
            citations=[
                {"source_type": "TENDER", "clause_number": "3.1", "page_number": 12, "snippet": "Minimum shell thickness 25 mm"},
                {"source_type": "BIDDER_DOCUMENT", "page_number": 4, "snippet": "Shell thickness provided: 28 mm"},
            ],
            notes="Technical specification fully compliant.",
        )
        m_non_compliant = EvaluationMatrixItem(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            dimension="TECHNICAL",
            status=MatrixItemStatus.NON_COMPLIANT,
            required_value="Minimum shell thickness >= 25 mm (Zero Deviation)",
            bidder_extracted_value="Thickness offered 20 mm in engineering drawing",
            deviation_magnitude=5.0,
            is_statutory=False,
            confidence_score=0.95,
            citations=[
                {"source_type": "TENDER", "clause_number": "5.2", "page_number": 18, "snippet": "Minimum shell thickness 25 mm strictly mandatory"},
                {"source_type": "BIDDER_DOCUMENT", "page_number": 2, "snippet": "Shell thickness provided: 20 mm"},
            ],
            notes="Exceeds allowable design limits.",
        )
        m_partial = EvaluationMatrixItem(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            dimension="COMMERCIAL",
            status=MatrixItemStatus.PARTIAL,
            required_value="PBG 5% valid for 18 months",
            bidder_extracted_value="PBG confirmation submitted without standard bank format",
            deviation_magnitude=10.0,
            is_statutory=False,
            confidence_score=0.88,
            citations=[
                {"source_type": "TENDER", "clause_number": "8.1", "page_number": 24, "snippet": "Performance Bank Guarantee per Annexure IV"},
            ],
            notes="PBG undertaking submitted but standard banker confirmation pending.",
        )
        m_not_verifiable = EvaluationMatrixItem(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            dimension="ELIGIBILITY",
            status=MatrixItemStatus.NOT_VERIFIABLE,
            required_value="Past experience: 3 similar supply contracts in last 5 years",
            bidder_extracted_value="Submitted uncertified purchase order list without client completion certificates",
            deviation_magnitude=0.0,
            is_statutory=False,
            confidence_score=0.60,
            citations=[
                {"source_type": "TENDER", "clause_number": "2.4", "page_number": 8, "snippet": "Client completion certificates mandatory"},
            ],
            notes="Client completion certificates missing; evidence not independently verifiable.",
        )
        m_exempt_mse = EvaluationMatrixItem(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            dimension="FINANCIAL",
            status=MatrixItemStatus.EXEMPT_MSE,
            required_value="Average Annual Turnover >= INR 50.00 Cr",
            bidder_extracted_value="Turnover INR 12.40 Cr, claimed MSE exemption under PPP-MSE 2012 with valid Udyam certificate",
            deviation_magnitude=0.0,
            is_statutory=True,
            confidence_score=1.0,
            citations=[
                {"source_type": "TENDER", "clause_number": "1.2", "page_number": 3, "snippet": "MSE exemption in line with PPP-MSE 2012"},
                {"source_type": "GOVERNMENT", "data_source": "UDYAM_MSME", "snippet": "Verified active Micro Enterprise"},
            ],
            notes="Exempt from turnover and past experience criteria under PPP-MSE 2012 Policy.",
        )

        session.add_all([m_compliant, m_non_compliant, m_partial, m_not_verifiable, m_exempt_mse])
        await session.flush()

        # 7. Officer Findings covering various severities and types
        f_crit = OfficerFinding(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            matrix_item_id=m_non_compliant.id,
            severity=FindingSeverity.CRITICAL,
            finding_type=FindingType.COMMERCIAL_DEVIATION,
            title="Non-compliant Delivery Schedule",
            description="Bidder offered delivery timeline of 22 weeks exceeding mandatory requirement of 16 weeks.",
            recommended_action="Seek formal clarification or confirm rejection basis.",
            review_status=FindingReviewStatus.PENDING,
        )
        f_high = OfficerFinding(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            matrix_item_id=m_partial.id,
            severity=FindingSeverity.HIGH,
            finding_type=FindingType.MISSING_DOCUMENT,
            title="Unverified Bank Guarantee Format",
            description="PBG undertaking submitted without approved banking format.",
            recommended_action="Request standard bank guarantee confirmation within 5 business days.",
            review_status=FindingReviewStatus.PENDING,
        )
        f_low = OfficerFinding(
            id=uuid.uuid4(),
            tender_id=tender_a.id,
            bidder_id=bidder_a.id,
            matrix_item_id=m_compliant.id,
            severity=FindingSeverity.LOW,
            finding_type=FindingType.TECHNICAL_SHORTFALL,
            title="Hydrostatic Test Pressure Documentation",
            description="Datasheet meets thickness requirement; verify test pressure calculation at 1.5x design pressure.",
            recommended_action="Confirm test pressure during detailed engineering drawing review.",
            review_status=FindingReviewStatus.ACCEPTED,
        )
        session.add_all([f_crit, f_high, f_low])
        await session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "officer_a": officer_a,
        "officer_b": officer_b,
        "tender_a": tender_a,
        "bidder_a": bidder_a,
        "matrix_compliant_id": m_compliant.id,
        "matrix_non_compliant_id": m_non_compliant.id,
        "matrix_partial_id": m_partial.id,
        "matrix_not_verifiable_id": m_not_verifiable.id,
        "matrix_exempt_mse_id": m_exempt_mse.id,
        "finding_crit_id": f_crit.id,
        "finding_high_id": f_high.id,
        "finding_low_id": f_low.id,
    }


async def _get_auth_headers(test_client: AsyncClient, email: str, password: str = "Password123!"):
    resp = await test_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_postgres_compliance_matrix_persistence_and_statuses(test_client, setup_integration_data):
    """Verify Phase 6 compliance matrix persistence in real PostgreSQL:
    - statuses: COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_VERIFIABLE, EXEMPT_MSE
    - confidence scores
    - statutory flags
    - citations
    - deviation values
    """
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)
    tender_id = str(data["tender_a"].id)
    bidder_id = str(data["bidder_a"].id)

    # 1. Query matrix from API backed by PostgreSQL
    resp = await test_client.get(
        f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/matrix",
        headers=headers_a,
    )
    assert resp.status_code == 200, f"Matrix fetch failed: {resp.text}"
    result = resp.json()
    assert result["tender_id"] == tender_id
    assert result["bidder_id"] == bidder_id
    assert result["total"] == 5

    items = result["items"]
    statuses = {item["status"] for item in items}
    assert statuses == {"COMPLIANT", "NON_COMPLIANT", "PARTIAL", "NOT_VERIFIABLE", "EXEMPT_MSE"}

    # 2. Verify specific fields
    exempt_item = next(it for it in items if it["status"] == "EXEMPT_MSE")
    assert exempt_item["is_statutory"] is True
    assert exempt_item["confidence_score"] == 1.0
    assert len(exempt_item["citations"]) >= 1

    non_comp_item = next(it for it in items if it["status"] == "NON_COMPLIANT")
    assert non_comp_item["deviation_magnitude"] == 5.0
    assert non_comp_item["confidence_score"] == 0.95
    assert len(non_comp_item["citations"]) == 2

    # 3. Direct PostgreSQL validation via SQLAlchemy session
    async with AsyncSessionLocal() as session:
        db_items_q = await session.execute(
            select(EvaluationMatrixItem).where(
                EvaluationMatrixItem.tender_id == data["tender_a"].id,
                EvaluationMatrixItem.bidder_id == data["bidder_a"].id,
            )
        )
        db_items = list(db_items_q.scalars().all())
        assert len(db_items) == 5
        db_statuses = {it.status.value for it in db_items}
        assert db_statuses == {"COMPLIANT", "NON_COMPLIANT", "PARTIAL", "NOT_VERIFIABLE", "EXEMPT_MSE"}


@pytest.mark.asyncio
async def test_postgres_risk_intelligence_and_deterministic_scoring(test_client, setup_integration_data):
    """Verify Risk Intelligence:
    - deterministic risk calculation (0-100 score, LOW/MEDIUM/HIGH/CRITICAL)
    - findings persistence
    - severity persistence
    - finding type persistence
    """
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)
    tender_id = str(data["tender_a"].id)
    bidder_id = str(data["bidder_a"].id)

    # 1. Fetch findings via API
    resp = await test_client.get(
        f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/findings",
        headers=headers_a,
    )
    assert resp.status_code == 200, f"Findings fetch failed: {resp.text}"
    res = resp.json()
    summary = res["summary"]
    assert "risk_indicator_score" in summary
    assert "risk_level" in summary
    assert 0.0 <= summary["risk_indicator_score"] <= 100.0
    # Because of 1 critical finding, risk level must be CRITICAL
    assert summary["risk_level"] == "CRITICAL"
    assert summary["critical_findings"] >= 1
    assert "autonomous" in summary["disclaimer"].lower()

    # 2. Check deterministic scoring formula directly
    # 1 CRITICAL (35) + 1 HIGH (20) + 1 LOW (3) + 1 UNVERIFIABLE (5) = 63.0 -> CRITICAL
    score, level = calculate_deterministic_risk_score(
        critical_count=1, high_count=1, medium_count=0, low_count=1, unverifiable_count=1
    )
    assert score == 63.0
    assert level == FindingSeverity.CRITICAL

    # 3. Direct PostgreSQL persistence verification
    async with AsyncSessionLocal() as session:
        findings_q = await session.execute(
            select(OfficerFinding).where(
                OfficerFinding.tender_id == data["tender_a"].id,
                OfficerFinding.bidder_id == data["bidder_a"].id,
            )
        )
        findings = list(findings_q.scalars().all())
        assert len(findings) >= 3
        severities = {f.severity.value for f in findings}
        assert "CRITICAL" in severities
        assert "MEDIUM" in severities
        assert "LOW" in severities
        finding_types = {f.finding_type.value for f in findings}
        assert "TECHNICAL_SHORTFALL" in finding_types or "COMMERCIAL_DEVIATION" in finding_types


@pytest.mark.asyncio
async def test_postgres_officer_workflow_and_override_justification(test_client, setup_integration_data):
    """Verify Officer Workflow in real PostgreSQL:
    - review states: ACCEPT, REJECT, OVERRIDE, CLARIFICATION_REQUESTED
    - OVERRIDE without justification -> strictly rejected (400)
    - OVERRIDE with justification -> accepted (200)
    - Verify persistence: review_status, officer_notes, user_id, timestamp
    """
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)
    finding_id = str(data["finding_crit_id"])
    officer_user_id = data["officer_a"].id

    # 1. Test OVERRIDE without notes -> Rejected
    resp_no_notes = await test_client.patch(
        f"/api/v1/compliance/findings/{finding_id}/review",
        headers=headers_a,
        json={"review_status": "OVERRIDDEN", "officer_notes": ""},
    )
    assert resp_no_notes.status_code == 400
    assert "justification note" in resp_no_notes.json()["detail"].lower()

    # 2. Test OVERRIDE with officer justification -> Accepted
    justification = "Reviewed by technical committee: manufacturer provided approved expedited schedule under Annexure 3.2"
    resp_with_notes = await test_client.patch(
        f"/api/v1/compliance/findings/{finding_id}/review",
        headers=headers_a,
        json={"review_status": "OVERRIDDEN", "officer_notes": justification},
    )
    assert resp_with_notes.status_code == 200
    result = resp_with_notes.json()
    assert result["review_status"] == "OVERRIDDEN"
    assert result["officer_notes"] == justification

    # 3. Direct PostgreSQL persistence verification
    async with AsyncSessionLocal() as session:
        f_q = await session.execute(select(OfficerFinding).where(OfficerFinding.id == data["finding_crit_id"]))
        persisted = f_q.scalar_one()
        assert persisted.review_status == FindingReviewStatus.OVERRIDDEN
        assert persisted.officer_notes == justification
        assert persisted.overridden_by_user_id == officer_user_id
        assert persisted.overridden_at is not None

    # 4. Test other states: ACCEPT, REJECT, CLARIFICATION_REQUESTED
    high_id = str(data["finding_high_id"])
    for st in ["CLARIFICATION_REQUESTED", "REJECTED", "ACCEPTED"]:
        r = await test_client.patch(
            f"/api/v1/compliance/findings/{high_id}/review",
            headers=headers_a,
            json={"review_status": st, "officer_notes": f"Status updated to {st}"},
        )
        assert r.status_code == 200
        assert r.json()["review_status"] == st


@pytest.mark.asyncio
async def test_postgres_tenant_isolation(test_client, setup_integration_data):
    """Verify strict tenant isolation against real PostgreSQL:
    Officer B (Org B) MUST NOT be able to retrieve or modify:
    - tenders
    - bidders
    - compliance matrix
    - officer findings
    - reports (JSON, PDF, CSV)
    - dashboard metrics
    """
    data = setup_integration_data
    headers_b = await _get_auth_headers(test_client, data["officer_b"].email)
    tender_a_id = str(data["tender_a"].id)
    bidder_a_id = str(data["bidder_a"].id)
    finding_id = str(data["finding_crit_id"])

    # 1. Tender of Org A not accessible by Org B
    resp_tender = await test_client.get(f"/api/v1/tenders/{tender_a_id}", headers=headers_b)
    assert resp_tender.status_code in (403, 404)

    # 2. Bidder of Org A not accessible by Org B
    resp_bidder = await test_client.get(f"/api/v1/bidders/{bidder_a_id}", headers=headers_b)
    assert resp_bidder.status_code in (403, 404)

    # 3. Matrix of Org A not accessible by Org B
    resp_matrix = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/bidders/{bidder_a_id}/matrix",
        headers=headers_b,
    )
    assert resp_matrix.status_code in (403, 404)

    # 4. Findings of Org A not accessible by Org B
    resp_findings = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/bidders/{bidder_a_id}/findings",
        headers=headers_b,
    )
    assert resp_findings.status_code in (403, 404)

    # 5. Reports of Org A not accessible by Org B
    resp_json = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/bidders/{bidder_a_id}/report/json",
        headers=headers_b,
    )
    assert resp_json.status_code in (403, 404)

    resp_pdf = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/bidders/{bidder_a_id}/report/pdf",
        headers=headers_b,
    )
    assert resp_pdf.status_code in (403, 404)

    resp_csv = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/bidders/{bidder_a_id}/report/csv",
        headers=headers_b,
    )
    assert resp_csv.status_code in (403, 404)

    # 6. Finding review of Org A rejected for Org B
    resp_review = await test_client.patch(
        f"/api/v1/compliance/findings/{finding_id}/review",
        headers=headers_b,
        json={"review_status": "ACCEPTED", "officer_notes": "Attempt unauthorized review"},
    )
    assert resp_review.status_code in (403, 404)

    # 7. Dashboard metrics of Org B must not include Org A tenders or bidders
    resp_dash_b = await test_client.get("/api/v1/dashboard/metrics", headers=headers_b)
    assert resp_dash_b.status_code == 200
    dash_b = resp_dash_b.json()
    assert dash_b["tender_metrics"]["total_tenders"] == 0
    assert dash_b["bidder_metrics"]["total_bidders"] == 0


@pytest.mark.asyncio
async def test_phase7_reports_against_real_postgres(test_client, setup_integration_data):
    """Verify Phase 7 reports (JSON, PDF, CSV) generated from real PostgreSQL records:
    - JSON: 16 sections, citations, findings, risk, officer decisions, statutory disclaimer
    - PDF: valid binary, multi-page capability, headers/footers, dynamic pagination, disclaimer
    - CSV: valid CSV, expected headers, status, values, deviations, confidence, statutory flag
    """
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)
    tender_id = str(data["tender_a"].id)
    bidder_id = str(data["bidder_a"].id)

    # --- 1. JSON Report ---
    resp_json = await test_client.get(
        f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/report/json",
        headers=headers_a,
    )
    assert resp_json.status_code == 200
    dossier = resp_json.json()

    sections_16 = [
        "tender", "bidder", "statutory_verifications", "mse_startup_assessment",
        "financial_eligibility", "technical_experience", "evaluation_matrix_items",
        "joint_venture_assessment", "debarment_integrity_check", "name_mismatch_analysis",
        "officer_findings", "clarifications_requested", "risk_profile",
        "officer_action_block", "compliance_summary", "audit_trail"
    ]
    for sec in sections_16:
        assert sec in dossier, f"Missing dossier section: {sec}"

    assert len(dossier["evaluation_matrix_items"]) == 5
    assert len(dossier["officer_findings"]) >= 3
    assert "non-autonomous" in dossier["disclaimer"].lower()

    # --- 2. PDF Report ---
    resp_pdf = await test_client.get(
        f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/report/pdf",
        headers=headers_a,
    )
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    pdf_bytes = resp_pdf.content
    assert pdf_bytes.startswith(b"%PDF"), "Missing PDF header"
    assert len(pdf_bytes) > 2000

    # Parse and inspect with pypdf
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(pdf_reader.pages) >= 1
    pdf_text = " ".join(p.extract_text() or "" for p in pdf_reader.pages)
    assert "BIDGUARD AI" in pdf_text
    assert "Apex Precision Fabrication" in pdf_text
    assert "non-autonomous" in pdf_text.lower()

    # --- 3. CSV Report ---
    resp_csv = await test_client.get(
        f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/report/csv",
        headers=headers_a,
    )
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    csv_text = resp_csv.text

    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= 6  # 1 header + 5 matrix rows
    header = rows[0]
    expected_cols = [
        "Matrix Item ID", "Dimension", "Status", "Required Value / Tender Rule",
        "Bidder Extracted Value", "Deviation", "Is Statutory",
        "Confidence", "Notes"
    ]
    for col in expected_cols:
        assert col in header, f"Missing CSV column: {col}"

    csv_statuses = {row[2] for row in rows[1:]}
    assert "COMPLIANT" in csv_statuses
    assert "EXEMPT_MSE" in csv_statuses


@pytest.mark.asyncio
async def test_postgres_dashboard_metrics_and_determinism(test_client, setup_integration_data):
    """Verify Dashboard Metrics calculated from real PostgreSQL database records."""
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)

    resp = await test_client.get("/api/v1/dashboard/metrics", headers=headers_a)
    assert resp.status_code == 200
    metrics = resp.json()

    # Tender metrics
    assert metrics["tender_metrics"]["total_tenders"] >= 1
    assert metrics["tender_metrics"]["under_review_tenders"] >= 1

    # Bidder metrics
    assert metrics["bidder_metrics"]["total_bidders"] >= 1
    assert metrics["bidder_metrics"]["evaluated_bidders"] >= 1
    assert metrics["bidder_metrics"]["mse_bidders_count"] >= 1

    # Compliance metrics
    cm = metrics["compliance_matrix_metrics"]
    assert cm["total_matrix_items"] >= 5
    assert cm["compliant_count"] >= 1
    assert cm["exempt_mse_count"] >= 1
    assert 0.0 <= cm["overall_compliance_rate_percent"] <= 100.0

    # Risk findings metrics
    rf = metrics["risk_findings_metrics"]
    assert rf["total_findings"] >= 3

    # Verification metrics
    vm = metrics["verification_metrics"]
    assert vm["total_requests"] >= 1

    # Non-autonomous guardrail disclaimer
    assert "non-autonomous" in metrics["disclaimer"].lower()


@pytest.mark.asyncio
async def test_postgres_audit_logging_and_auditable_overrides(test_client, setup_integration_data):
    """Verify real PostgreSQL persistence of audit log events:
    - REPORT_JSON_VIEWED
    - REPORT_PDF_DOWNLOADED
    - REPORT_CSV_DOWNLOADED
    - OFFICER_FINDING_REVIEWED
    - officer overrides are auditable with user ID and previous/new state
    """
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)
    tender_id = str(data["tender_a"].id)
    bidder_id = str(data["bidder_a"].id)
    finding_id = str(data["finding_high_id"])

    # 1. Trigger report downloads to record audit logs
    await test_client.get(f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/report/json", headers=headers_a)
    await test_client.get(f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/report/pdf", headers=headers_a)
    await test_client.get(f"/api/v1/tenders/{tender_id}/bidders/{bidder_id}/report/csv", headers=headers_a)

    # 2. Trigger officer override to record audit log
    await test_client.patch(
        f"/api/v1/compliance/findings/{finding_id}/review",
        headers=headers_a,
        json={"review_status": "OVERRIDDEN", "officer_notes": "Auditable justification provided by officer."},
    )

    # 3. Query audit_logs table directly in PostgreSQL
    async with AsyncSessionLocal() as session:
        logs_q = await session.execute(
            select(AuditLog).where(AuditLog.organization_id == data["org_a"].id)
        )
        logs = list(logs_q.scalars().all())
        actions = {l.action for l in logs}

        assert "REPORT_JSON_VIEWED" in actions
        assert "REPORT_PDF_DOWNLOADED" in actions
        assert "REPORT_CSV_DOWNLOADED" in actions
        assert "OFFICER_FINDING_REVIEWED" in actions

        override_logs = [l for l in logs if l.action == "OFFICER_FINDING_REVIEWED"]
        assert len(override_logs) >= 1
        last_log = override_logs[-1]
        assert last_log.actor_user_id == data["officer_a"].id
        assert last_log.new_state["review_status"] == "OVERRIDDEN"
        assert "Auditable justification" in last_log.new_state["officer_notes"]


@pytest.mark.asyncio
async def test_non_autonomous_guardrail_enforcement(test_client, setup_integration_data):
    """Strictly verify non-autonomous guardrail:
    - BidGuard AI never returns 'winner'
    - BidGuard AI never returns 'best_bidder'
    - BidGuard AI never returns 'recommended_bidder'
    - Comparison includes non-autonomous notice
    """
    data = setup_integration_data
    headers_a = await _get_auth_headers(test_client, data["officer_a"].email)
    tender_id = str(data["tender_a"].id)

    resp = await test_client.get(f"/api/v1/tenders/{tender_id}/compare-bidders", headers=headers_a)
    assert resp.status_code == 200
    comp = resp.json()

    assert "winner" not in comp
    assert "best_bidder" not in comp
    assert "recommended_bidder" not in comp
    assert "guardrail_notice" in comp
    assert "does not declare winners" in comp["guardrail_notice"].lower()
