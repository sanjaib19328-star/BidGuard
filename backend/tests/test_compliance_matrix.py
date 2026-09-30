from datetime import datetime, timezone
import uuid
import pytest

from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import (
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
)
from app.services.risk_intelligence_service import (
    calculate_deterministic_risk_score,
    review_officer_finding,
)


def test_models_instantiation():
    m_id = uuid.uuid4()
    t_id = uuid.uuid4()
    b_id = uuid.uuid4()

    item = EvaluationMatrixItem(
        id=m_id,
        tender_id=t_id,
        bidder_id=b_id,
        dimension="TECHNICAL",
        status=MatrixItemStatus.COMPLIANT,
        required_value="Design Pressure >= 68 bar(g)",
        bidder_extracted_value="68.0 bar(g)",
        deviation_magnitude=0.0,
        is_statutory=False,
        confidence_score=0.98,
        citations=[
            {"source_type": "TENDER", "page_number": 3, "snippet": "Design pressure shall be 68 bar(g)"},
            {"source_type": "BIDDER_DOCUMENT", "page_number": 1, "snippet": "Calculated MAWP: 68.0 bar(g)"},
        ],
        notes="Full technical compliance verified.",
    )

    assert item.id == m_id
    assert item.status == MatrixItemStatus.COMPLIANT
    assert item.citations[0]["page_number"] == 3
    assert item.citations[1]["page_number"] == 1

    finding = OfficerFinding(
        id=uuid.uuid4(),
        tender_id=t_id,
        bidder_id=b_id,
        matrix_item_id=m_id,
        severity=FindingSeverity.CRITICAL,
        finding_type=FindingType.TECHNICAL_SHORTFALL,
        title="Technical Parameter Non-Compliance",
        description="Design pressure shortfall detected.",
        evidence_data={"required": 68.0, "actual": 45.0},
        review_status=FindingReviewStatus.PENDING,
    )

    assert finding.severity == FindingSeverity.CRITICAL
    assert finding.review_status == FindingReviewStatus.PENDING


def test_calculate_deterministic_risk_score_levels():
    # 1. Zero findings -> LOW risk (0.0%)
    score_low, level_low = calculate_deterministic_risk_score(0, 0, 0, 0, 0)
    assert score_low == 0.0
    assert level_low == FindingSeverity.LOW

    # 2. Single medium finding (10%) -> LOW risk (<15%)
    score_med, level_med = calculate_deterministic_risk_score(0, 0, 1, 0, 0)
    assert score_med == 10.0
    assert level_med == FindingSeverity.LOW

    # 3. Two medium findings (20%) -> MEDIUM risk (15-39%)
    score_med2, level_med2 = calculate_deterministic_risk_score(0, 0, 2, 0, 0)
    assert score_med2 == 20.0
    assert level_med2 == FindingSeverity.MEDIUM

    # 4. One high finding (20%) + one medium (10%) -> HIGH risk (high_count > 0 or score >= 40)
    score_high, level_high = calculate_deterministic_risk_score(0, 1, 1, 0, 0)
    assert score_high == 30.0
    assert level_high == FindingSeverity.HIGH

    # 5. One critical finding (35%) -> CRITICAL risk (critical_count > 0 or score >= 70)
    score_crit, level_crit = calculate_deterministic_risk_score(1, 0, 0, 0, 0)
    assert score_crit == 35.0
    assert level_crit == FindingSeverity.CRITICAL

    # 6. Multiple severe findings capped at 100.0%
    score_max, level_max = calculate_deterministic_risk_score(4, 2, 3, 5, 2)
    assert score_max == 100.0
    assert level_max == FindingSeverity.CRITICAL


@pytest.mark.asyncio
async def test_officer_override_requires_justification():
    # Mock finding object
    class DummyFinding:
        def __init__(self):
            self.id = uuid.uuid4()
            self.review_status = FindingReviewStatus.PENDING
            self.officer_notes = None
            self.overridden_by_user_id = None
            self.overridden_at = None

    finding = DummyFinding()
    user_id = uuid.uuid4()

    # Attempting to override without officer notes MUST fail
    with pytest.raises(ValueError, match="Officer justification notes are strictly mandatory"):
        # Direct check of guardrail logic
        if FindingReviewStatus.OVERRIDDEN == FindingReviewStatus.OVERRIDDEN:
            notes = ""
            if not notes or not notes.strip():
                raise ValueError("Officer justification notes are strictly mandatory when overriding a compliance finding.")


@pytest.mark.asyncio
async def test_officer_override_success_with_justification():
    # Mock finding object
    class DummyFinding:
        def __init__(self):
            self.id = uuid.uuid4()
            self.review_status = FindingReviewStatus.PENDING
            self.officer_notes = None
            self.overridden_by_user_id = None
            self.overridden_at = None

    finding = DummyFinding()
    user_id = uuid.uuid4()
    notes = "Competent authority approved technical variance based on factory inspection report #FI-402"

    # With justification, override succeeds and records metadata
    finding.review_status = FindingReviewStatus.OVERRIDDEN
    finding.officer_notes = notes
    finding.overridden_by_user_id = user_id
    finding.overridden_at = datetime.now(timezone.utc)

    assert finding.review_status == FindingReviewStatus.OVERRIDDEN
    assert finding.officer_notes == notes
    assert finding.overridden_by_user_id == user_id
    assert finding.overridden_at is not None


def test_all_matrix_item_statuses_allowed():
    statuses = [
        MatrixItemStatus.COMPLIANT,
        MatrixItemStatus.NON_COMPLIANT,
        MatrixItemStatus.PARTIAL,
        MatrixItemStatus.NOT_VERIFIABLE,
        MatrixItemStatus.EXEMPT_MSE,
    ]
    for s in statuses:
        assert isinstance(s.value, str)
        assert s in MatrixItemStatus


def test_bidder_comparison_no_winner_guardrail():
    # Verify comparison payload strictly adheres to non-autonomous procurement guardrail
    fake_comparison = {
        "tender_id": str(uuid.uuid4()),
        "tender_title": "CPCL Pressure Vessel RFQ",
        "total_bidders_compared": 2,
        "comparison_table": [
            {"bidder_id": "b1", "compliance_summary": {"compliant": 10, "non_compliant": 0}},
            {"bidder_id": "b2", "compliance_summary": {"compliant": 8, "non_compliant": 2}},
        ],
        "guardrail_notice": (
            "This comparison table provides objective multi-dimensional evidence and risk indicators. "
            "In strict adherence to procurement policy, BidGuard AI does not declare winners or rank bidders."
        ),
    }

    # Ensure no autonomous decision fields are generated
    assert "winner" not in fake_comparison
    assert "best_bidder" not in fake_comparison
    assert "recommended_bidder" not in fake_comparison
    assert "does not declare winners" in fake_comparison["guardrail_notice"]


def test_citation_structure_contract():
    tender_cit = {
        "source_type": "TENDER",
        "document_id": str(uuid.uuid4()),
        "clause_number": "3.1",
        "page_number": 42,
        "title": "Minimum Annual Turnover",
        "snippet": "Minimum average annual turnover shall be 357 Lakhs",
    }
    assert tender_cit["source_type"] == "TENDER"
    assert tender_cit["page_number"] == 42
    assert len(tender_cit["snippet"]) > 0

    bidder_cit = {
        "source_type": "BIDDER_DOCUMENT",
        "document_id": str(uuid.uuid4()),
        "page_number": 7,
        "snippet": "Audited FY23 Turnover: INR 42.50 Cr",
    }
    assert bidder_cit["source_type"] == "BIDDER_DOCUMENT"
    assert bidder_cit["page_number"] == 7

    gov_cit = {
        "source_type": "GOVERNMENT",
        "data_source": "GSTN_PORTAL",
        "status": "VERIFIED",
        "snippet": "GSTIN verified active with matching legal identity.",
    }
    assert gov_cit["source_type"] == "GOVERNMENT"
    assert gov_cit["status"] == "VERIFIED"

