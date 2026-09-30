import uuid
import pytest

from app.models.clause import TenderClause
from app.models.enums import (
    ClauseCategory,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    VerificationMethod,
)
from app.services.requirement_extraction_service import (
    build_requirement_signature,
    detect_applicability,
    detect_mandatory,
    extract_numeric_and_unit,
    extract_operator,
    extract_period,
    extract_requirements_from_clause,
    infer_evidence_and_method,
    is_requirement_candidate,
)


def test_candidate_detection():
    """Verify requirement candidate detection filters preamble and flags obligations."""
    # Preamble should not be candidate
    assert not is_requirement_candidate("This tender document was published on the GeM portal.")
    assert not is_requirement_candidate("Table of Contents\nSection 1: General")

    # Obligations should be candidates
    assert is_requirement_candidate("The bidder shall have an average annual turnover of at least ₹10 crore.")
    assert is_requirement_candidate("Valid GSTIN and PAN registration must be submitted.")
    assert is_requirement_candidate("Delivery shall be completed within 60 days.")


def test_numeric_and_unit_extraction():
    """Test extracting numbers, units, and currencies across Indian procurement formats."""
    # ₹10 crore
    val, unit, curr = extract_numeric_and_unit("Average turnover of at least ₹10 crore.")
    assert val == 10.0
    assert unit == "CRORE_INR"
    assert curr == "INR"

    # Rs. 50 Lakhs
    val, unit, curr = extract_numeric_and_unit("Net worth exceeding Rs. 50 Lakhs.")
    assert val == 50.0
    assert unit == "LAKH_INR"
    assert curr == "INR"

    # INR 5 Cr
    val, unit, curr = extract_numeric_and_unit("Turnover not less than INR 5 Cr.")
    assert val == 5.0
    assert unit == "CRORE_INR"
    assert curr == "INR"

    # 5 years
    val, unit, curr = extract_numeric_and_unit("Minimum 5 years of manufacturing experience.")
    assert val == 5.0
    assert unit == "YEARS"
    assert curr is None

    # 90 days
    val, unit, curr = extract_numeric_and_unit("Delivery within 90 days from order date.")
    assert val == 90.0
    assert unit == "DAYS"

    # 25%
    val, unit, curr = extract_numeric_and_unit("Earnest Money Deposit of 25% shall apply.")
    assert val == 25.0
    assert unit == "PERCENT"

    # Word numbers: three years
    val, unit, curr = extract_numeric_and_unit("Prior experience of at least three years.")
    assert val == 3.0
    assert unit == "YEARS"


def test_operator_extraction():
    """Verify operator mapping for various constraint phrases."""
    assert extract_operator("Turnover of at least ₹10 crore") == ">="
    assert extract_operator("Minimum 5 years of experience") == ">="
    assert extract_operator("Turnover not less than INR 5 Cr") == ">="
    assert extract_operator("Turnover more than ₹500 lakh") == ">"
    assert extract_operator("Delivery within 60 days") == "<="
    assert extract_operator("Maximum tolerance not exceeding 2mm") == "<="
    assert extract_operator("GST registration is mandatory") == "REQUIRED"
    assert extract_operator("Joint venture is strictly forbidden") == "PROHIBITED"
    assert extract_operator("Catalog submission is optional") == "OPTIONAL"


def test_period_extraction():
    """Verify time period extraction from text."""
    assert extract_period("during the last three financial years") == "LAST_3_FINANCIAL_YEARS"
    assert extract_period("in the preceding 5 years") == "PREVIOUS_5_YEARS"
    assert extract_period("delivery within 60 days from award") == "WITHIN_60_DAYS"
    assert extract_period("bid valid for 120 days from opening") == "VALIDITY_120_DAYS"


def test_mandatory_detection():
    """Verify mandatory status is True for modal obligations, False for optional, None for ambiguous."""
    assert detect_mandatory("The bidder shall provide valid GSTIN.") is True
    assert detect_mandatory("Bidders must possess ASME certification.") is True
    assert detect_mandatory("Submission of ISO certificate is optional.") is False
    assert detect_mandatory("Catalog may be provided by vendor.") is False
    assert detect_mandatory("General information regarding tender process.") is None


def test_applicability_detection():
    """Verify applicability classification and conditional extraction."""
    # OEM
    app, cond = detect_applicability("The OEM shall provide manufacturer warranty.")
    assert app == RequirementApplicability.OEM
    assert cond is None

    # Authorized dealer
    app, cond = detect_applicability("The authorized dealer must submit authorization letter.")
    assert app == RequirementApplicability.AUTHORIZED_DEALER

    # MSME
    app, cond = detect_applicability("Applicable to MSME bidders claiming fee exemption.")
    assert app == RequirementApplicability.MSME

    # Conditional
    app, cond = detect_applicability("If the bidder is an authorized dealer, OEM authorization must be submitted.")
    assert app == RequirementApplicability.CONDITIONAL
    assert "authorized dealer" in cond.lower()

    # Default
    app, cond = detect_applicability("All bidders shall possess valid PAN card.")
    assert app == RequirementApplicability.ALL_BIDDERS


def test_evidence_and_method_inference():
    """Test evidence and verification method inference across requirement types."""
    ev, method, risk = infer_evidence_and_method(RequirementType.MIN_TURNOVER)
    assert "FINANCIAL_STATEMENTS" in ev
    assert method == VerificationMethod.DOCUMENT
    assert risk == RiskHint.HIGH

    ev, method, risk = infer_evidence_and_method(RequirementType.GST_REGISTRATION)
    assert "GST_CERTIFICATE" in ev
    assert method == VerificationMethod.DOCUMENT
    assert risk == RiskHint.HIGH

    ev, method, risk = infer_evidence_and_method(RequirementType.DELIVERY_PERIOD)
    assert method == VerificationMethod.RULE
    assert risk == RiskHint.MEDIUM


def test_multi_requirement_clause_splitting():
    """Verify that a single clause with multiple requirements splits into separate structured records."""
    dummy_clause = TenderClause(
        id=uuid.uuid4(),
        tender_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        page_number=1,
        clause_number="4.1",
        title="Statutory and Financial Requirements",
        clause_text="Bidder shall submit valid GSTIN certificate and PAN card, and must have average annual turnover of at least ₹10 crore.",
        category=ClauseCategory.STATUTORY,
        sequence_order=1,
        extraction_method="RULE_BASED",
        confidence=0.90,
    )

    reqs = extract_requirements_from_clause(dummy_clause)
    req_types = [r["requirement_type"] for r in reqs]

    assert RequirementType.GST_REGISTRATION in req_types
    assert RequirementType.PAN_REQUIRED in req_types
    assert RequirementType.MIN_TURNOVER in req_types
    assert len(reqs) >= 3


def test_requirement_signature_stability():
    """Test that build_requirement_signature produces identical SHA-256 for identical inputs."""
    t_id = uuid.uuid4()
    c_id = uuid.uuid4()

    sig1 = build_requirement_signature(
        tender_id=t_id,
        clause_id=c_id,
        req_type=RequirementType.MIN_TURNOVER,
        description="Minimum annual turnover",
        operator=">=",
        value_numeric=10.0,
        value_text=None,
        unit="CRORE_INR",
        currency="INR",
        period="LAST_3_FINANCIAL_YEARS",
        applicability=RequirementApplicability.ALL_BIDDERS,
        applicability_condition=None,
    )

    sig2 = build_requirement_signature(
        tender_id=t_id,
        clause_id=c_id,
        req_type=RequirementType.MIN_TURNOVER,
        description="Minimum annual turnover",
        operator=">=",
        value_numeric=10.0,
        value_text=None,
        unit="CRORE_INR",
        currency="INR",
        period="LAST_3_FINANCIAL_YEARS",
        applicability=RequirementApplicability.ALL_BIDDERS,
        applicability_condition=None,
    )

    assert sig1 == sig2
    assert len(sig1) == 64
