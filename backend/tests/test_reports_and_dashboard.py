from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.models.audit import AuditLog
from app.models.bidder import Bidder
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import (
    DataSourceType,
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
    TenderStatus,
    VerificationResultStatus,
)
from app.models.tender import Tender
from app.models.verification import VerificationRequest, VerificationResult
from app.services.dashboard_service import get_procurement_dashboard_metrics
from app.services.report_service import (
    build_compliance_dossier_data,
    generate_compliance_csv_report,
    generate_compliance_pdf_report,
)


@pytest.fixture
def mock_dossier_data():
    org_id = uuid.uuid4()
    tender_id = uuid.uuid4()
    bidder_id = uuid.uuid4()
    user_id = uuid.uuid4()

    tender = Tender(
        id=tender_id,
        organization_id=org_id,
        tender_number="GEM/2024/B/998877",
        title="Supply and Commissioning of Multi-Parameter Patient Monitors",
        procuring_entity="AIIMS Procurement Cell",
        department="Biomedical Engineering",
        tender_type="Open Tender",
        status=TenderStatus.UNDER_REVIEW,
    )
    setattr(tender, "estimated_value", 15000000.0)

    bidder = Bidder(
        id=bidder_id,
        organization_id=org_id,
        legal_name="Apex Healthcare Equipments Pvt Ltd",
        trade_name="Apex Meditech",
        pan="AABCA1234F",
        gstin="07AABCA1234F1Z5",
        udyam_registration_number="UDYAM-DL-01-0012345",
        is_mse=True,
    )

    matrix_item1 = EvaluationMatrixItem(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        dimension="TECHNICAL",
        status=MatrixItemStatus.COMPLIANT,
        required_value="Touchscreen Display >= 12.1 inches",
        bidder_extracted_value="15.6 inch high-resolution TFT display",
        deviation_magnitude=0.0,
        is_statutory=False,
        confidence_score=0.97,
        citations=[
            {"source_type": "TENDER", "page_number": 14, "snippet": "Display size must be min 12.1 inch"},
            {"source_type": "BIDDER_DOCUMENT", "page_number": 4, "snippet": "15.6 inch capacitive touchscreen"},
        ],
        notes="Technical parameter fully compliant.",
    )

    matrix_item2 = EvaluationMatrixItem(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        dimension="FINANCIAL",
        status=MatrixItemStatus.EXEMPT_MSE,
        required_value="Annual Turnover >= INR 50 Lakhs",
        bidder_extracted_value="Turnover INR 35 Lakhs with Udyam Certificate",
        deviation_magnitude=0.0,
        is_statutory=True,
        confidence_score=1.0,
        citations=[
            {"source_type": "TENDER", "page_number": 8, "snippet": "MSE bidders exempt from prior turnover criteria"},
            {"source_type": "BIDDER_DOCUMENT", "page_number": 2, "snippet": "Udyam Registration UDYAM-DL-01-0012345"},
        ],
        notes="Exempted under Public Procurement Policy for MSEs 2012.",
    )

    finding1 = OfficerFinding(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        matrix_item_id=matrix_item1.id,
        severity=FindingSeverity.LOW,
        finding_type=FindingType.TECHNICAL_SHORTFALL,
        title="Battery Backup Runtime Clarification",
        description="Verify battery operating runtime under full waveform acquisition.",
        recommended_action="Seek manufacturer battery test datasheet.",
        review_status=FindingReviewStatus.ACCEPTED,
    )

    finding2 = OfficerFinding(
        id=uuid.uuid4(),
        tender_id=tender_id,
        bidder_id=bidder_id,
        matrix_item_id=matrix_item2.id,
        severity=FindingSeverity.HIGH,
        finding_type=FindingType.COMMERCIAL_DEVIATION,
        title="Warranty Period Mismatch",
        description="Bidder offered 3 years warranty against 5 years tender requirement.",
        recommended_action="Seek formal warranty extension confirmation.",
        review_status=FindingReviewStatus.OVERRIDDEN,
        officer_notes="Officer verified bidder uploaded separate 2-year AMC extension letter in Annexure VI.",
        overridden_by_user_id=user_id,
        overridden_at=datetime.now(timezone.utc),
    )

    v_req = VerificationRequest(
        id=uuid.uuid4(),
        organization_id=org_id,
        bidder_id=bidder_id,
        tender_id=tender_id,
        verification_type=DataSourceType.UDYAM_MSME,
        identifier_value="UDYAM-DL-01-0012345",
    )
    v_res = VerificationResult(
        id=uuid.uuid4(),
        verification_request_id=v_req.id,
        bidder_id=bidder_id,
        source_type=DataSourceType.UDYAM_MSME,
        status=VerificationResultStatus.VERIFIED,
        name_match_score=0.98,
        sanitized_response={
            "enterprise_name": "Apex Healthcare Equipments Pvt Ltd",
            "major_activity": "Manufacturing",
            "enterprise_type": "Micro",
        },
    )
    v_req.result = v_res

    audit = AuditLog(
        id=uuid.uuid4(),
        organization_id=org_id,
        action="OFFICER_FINDING_REVIEWED",
        entity_type="officer_finding",
        entity_id=str(finding2.id),
        actor_user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )

    return {
        "org_id": org_id,
        "tender_id": tender_id,
        "bidder_id": bidder_id,
        "tender": tender,
        "bidder": bidder,
        "matrix_items": [matrix_item1, matrix_item2],
        "findings": [finding1, finding2],
        "verifications": [v_res],
        "audit_logs": [audit],
    }


def create_mock_session(data):
    session = AsyncMock()

    async def mock_execute(query):
        mock_result = MagicMock()
        q_str = str(query)

        # 1. Tender
        if "FROM tenders" in q_str:
            mock_result.scalar_one_or_none.return_value = data["tender"]
            mock_result.scalars.return_value.all.return_value = [data["tender"]]
            return mock_result

        # 2. Bidder
        if "FROM bidders" in q_str:
            mock_result.scalar_one_or_none.return_value = data["bidder"]
            mock_result.scalars.return_value.all.return_value = [data["bidder"]]
            return mock_result

        # 3. Evaluation Matrix Items
        if "FROM evaluation_matrix_items" in q_str:
            mock_result.scalars.return_value.all.return_value = data["matrix_items"]
            return mock_result

        # 4. Officer Findings
        if "FROM officer_findings" in q_str:
            mock_result.scalars.return_value.all.return_value = data["findings"]
            return mock_result

        # 5. Verification Results
        if "FROM verification_results" in q_str:
            mock_result.scalars.return_value.all.return_value = data["verifications"]
            return mock_result

        # 6. Audit Logs
        if "FROM audit_logs" in q_str:
            mock_result.scalars.return_value.all.return_value = data["audit_logs"]
            return mock_result

        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        return mock_result

    session.execute.side_effect = mock_execute
    return session


@pytest.mark.asyncio
async def test_build_compliance_dossier_data_all_sections(mock_dossier_data):
    session = create_mock_session(mock_dossier_data)
    dossier = await build_compliance_dossier_data(
        session=session,
        tender_id=mock_dossier_data["tender_id"],
        bidder_id=mock_dossier_data["bidder_id"],
        organization_id=mock_dossier_data["org_id"],
    )

    # Verify all 16 required sections exist
    required_sections = [
        "generated_at",
        "disclaimer",
        "tender",
        "bidder",
        "compliance_summary",
        "risk_profile",
        "evaluation_matrix_items",
        "officer_findings",
        "statutory_verifications",
        "mse_startup_assessment",
        "financial_eligibility",
        "technical_experience",
        "joint_venture_assessment",
        "debarment_integrity_check",
        "name_mismatch_analysis",
        "clarifications_requested",
        "audit_trail",
        "officer_action_block",
    ]
    for section in required_sections:
        assert section in dossier, f"Missing section: {section}"

    # Verify Non-Autonomous Disclaimer
    assert "non-autonomous" in dossier["disclaimer"].lower()
    assert "advisory" in dossier["disclaimer"].lower()

    # Verify Tender & Bidder mapping
    assert dossier["tender"]["tender_number"] == "GEM/2024/B/998877"
    assert dossier["bidder"]["legal_name"] == "Apex Healthcare Equipments Pvt Ltd"
    assert dossier["bidder"]["is_mse"] is True

    # Verify Compliance Summary Counts
    summary = dossier["compliance_summary"]
    assert summary["total_rules_evaluated"] == 2
    assert summary["compliant_count"] == 1
    assert summary["exempt_mse_count"] == 1

    # Verify Findings and Officer Overrides
    findings = dossier["officer_findings"]
    assert len(findings) == 2
    overridden = [f for f in findings if f["review_status"] == FindingReviewStatus.OVERRIDDEN.value]
    assert len(overridden) == 1
    assert "Annexure VI" in overridden[0]["officer_notes"]


@pytest.mark.asyncio
async def test_generate_compliance_csv_report(mock_dossier_data):
    session = create_mock_session(mock_dossier_data)
    dossier = await build_compliance_dossier_data(
        session=session,
        tender_id=mock_dossier_data["tender_id"],
        bidder_id=mock_dossier_data["bidder_id"],
        organization_id=mock_dossier_data["org_id"],
    )

    csv_content = generate_compliance_csv_report(dossier)

    assert isinstance(csv_content, str)
    assert len(csv_content) > 100
    # Check headers
    assert "Matrix Item ID" in csv_content
    assert "Dimension" in csv_content
    assert "Status" in csv_content
    assert "Required Value / Tender Rule" in csv_content
    assert "Bidder Extracted Value" in csv_content
    # Check rows
    assert "Touchscreen Display >= 12.1 inches" in csv_content
    assert "Annual Turnover >= INR 50 Lakhs" in csv_content
    assert "EXEMPT_MSE" in csv_content


@pytest.mark.asyncio
async def test_generate_compliance_pdf_report(mock_dossier_data):
    session = create_mock_session(mock_dossier_data)
    dossier = await build_compliance_dossier_data(
        session=session,
        tender_id=mock_dossier_data["tender_id"],
        bidder_id=mock_dossier_data["bidder_id"],
        organization_id=mock_dossier_data["org_id"],
    )

    pdf_bytes = generate_compliance_pdf_report(dossier)

    assert isinstance(pdf_bytes, bytes)
    # Valid PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF")
    # Substantial PDF document generated
    assert len(pdf_bytes) > 2000


@pytest.mark.asyncio
async def test_dashboard_metrics_aggregation():
    org_id = uuid.uuid4()
    session = AsyncMock()

    call_count = 0

    async def mock_dashboard_execute(query):
        nonlocal call_count
        call_count += 1
        mock_result = MagicMock()
        q_str = str(query)

        if "FROM tenders" in q_str and "GROUP BY tenders.status" in q_str:
            mock_result.all.return_value = [
                (TenderStatus.UNDER_REVIEW, 3),
                (TenderStatus.READY, 2),
                (TenderStatus.COMPLETED, 1),
            ]
            return mock_result

        if "FROM bidders" in q_str:
            # bidder counts
            row = MagicMock()
            row.total = 10
            row.mse_count = 4
            mock_result.one_or_none.return_value = row
            return mock_result

        if "FROM evaluation_matrix_items" in q_str and "distinct" in q_str.lower():
            # evaluated bidders
            mock_result.scalar_one.return_value = 7
            return mock_result

        if "FROM evaluation_matrix_items" in q_str and "GROUP BY evaluation_matrix_items.status" in q_str:
            mock_result.all.return_value = [
                (MatrixItemStatus.COMPLIANT, 18),
                (MatrixItemStatus.EXEMPT_MSE, 4),
                (MatrixItemStatus.NON_COMPLIANT, 2),
            ]
            return mock_result

        if "FROM officer_findings" in q_str and "GROUP BY officer_findings.severity" in q_str:
            mock_result.all.return_value = [
                (FindingSeverity.CRITICAL, 1),
                (FindingSeverity.HIGH, 2),
                (FindingSeverity.LOW, 5),
            ]
            return mock_result

        if "FROM officer_findings" in q_str and "GROUP BY officer_findings.review_status" in q_str:
            mock_result.all.return_value = [
                (FindingReviewStatus.PENDING, 3),
                (FindingReviewStatus.ACCEPTED, 4),
                (FindingReviewStatus.OVERRIDDEN, 1),
            ]
            return mock_result

        if "unresolved" in q_str.lower() or ("officer_findings.severity IN" in q_str):
            mock_result.scalar_one.return_value = 2
            return mock_result

        if "FROM verification_requests" in q_str:
            mock_result.all.return_value = [
                (DataSourceType.GSTN_PORTAL, 8),
                (DataSourceType.UDYAM_MSME, 6),
            ]
            return mock_result

        if "FROM verification_results" in q_str:
            mock_result.all.return_value = [
                (VerificationResultStatus.VERIFIED, 12),
                (VerificationResultStatus.ERROR, 2),
            ]
            return mock_result

        if "FROM audit_logs" in q_str:
            audit = AuditLog(
                id=uuid.uuid4(),
                organization_id=org_id,
                action="COMPLIANCE_EVALUATION",
                entity_type="compliance_matrix",
                created_at=datetime.now(timezone.utc),
            )
            mock_result.scalars.return_value.all.return_value = [audit]
            return mock_result

        mock_result.all.return_value = []
        mock_result.scalar_one.return_value = 0
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        return mock_result

    session.execute.side_effect = mock_dashboard_execute

    metrics = await get_procurement_dashboard_metrics(
        session=session,
        organization_id=org_id,
    )

    assert "tender_metrics" in metrics
    assert metrics["tender_metrics"]["total_tenders"] == 6
    assert metrics["tender_metrics"]["under_review_tenders"] == 3
    assert metrics["tender_metrics"]["completed_tenders"] == 1

    assert "bidder_metrics" in metrics
    assert metrics["bidder_metrics"]["total_bidders"] == 10
    assert metrics["bidder_metrics"]["evaluated_bidders"] == 7
    assert metrics["bidder_metrics"]["pending_bidders"] == 3
    assert metrics["bidder_metrics"]["mse_bidders_count"] == 4

    assert "compliance_matrix_metrics" in metrics
    assert metrics["compliance_matrix_metrics"]["total_matrix_items"] == 24
    assert metrics["compliance_matrix_metrics"]["compliant_count"] == 18
    assert metrics["compliance_matrix_metrics"]["exempt_mse_count"] == 4
    # compliance rate: (18+4)/24 = 22/24 * 100 = 91.7%
    assert metrics["compliance_matrix_metrics"]["overall_compliance_rate_percent"] == 91.7

    assert "risk_findings_metrics" in metrics
    assert metrics["risk_findings_metrics"]["total_findings"] == 8
    assert metrics["risk_findings_metrics"]["unresolved_critical_high"] == 2

    assert "verification_metrics" in metrics
    assert metrics["verification_metrics"]["total_requests"] == 14

    assert "recent_activity" in metrics
    assert len(metrics["recent_activity"]) == 1
    assert metrics["recent_activity"][0]["action"] == "COMPLIANCE_EVALUATION"

    assert "disclaimer" in metrics
    assert "non-autonomous" in metrics["disclaimer"].lower()
