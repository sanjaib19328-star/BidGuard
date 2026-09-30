import uuid
import pytest

from app.models.compliance_rule import ComplianceRule
from app.models.enums import (
    ClauseCategory,
    ComplianceRuleType,
    EvaluationStatus,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    VerificationMethod,
)
from app.models.requirement import TenderRequirement
from app.services.compliance_evaluation_service import (
    evaluate_single_rule,
    evaluate_numeric_threshold,
    evaluate_numeric_range,
    evaluate_required_document,
    evaluate_boolean_requirement,
    evaluate_existence_check,
    evaluate_date_limit,
    normalize_numeric_value,
)


def _build_rule(
    rule_type: ComplianceRuleType,
    config: dict,
    desc: str = "Test Rule",
    applicability: RequirementApplicability = RequirementApplicability.ALL_BIDDERS,
) -> ComplianceRule:
    req = TenderRequirement(
        id=uuid.uuid4(),
        tender_id=uuid.uuid4(),
        clause_id=uuid.uuid4(),
        category=ClauseCategory.FINANCIAL,
        requirement_type=RequirementType.MIN_TURNOVER,
        description=desc,
        verification_method=VerificationMethod.RULE,
        risk_hint=RiskHint.MEDIUM,
        applicability=applicability,
        mandatory=True,
    )
    rule = ComplianceRule(
        id=uuid.uuid4(),
        tender_id=req.tender_id,
        requirement_id=req.id,
        rule_type=rule_type,
        rule_configuration=config,
        description=desc,
        enabled=True,
    )
    rule.requirement = req
    return rule


def test_unit_normalization():
    """Verify INR currency and time conversions to base values."""
    # 10 Crore = 100,000,000 INR
    norm_val, base_unit = normalize_numeric_value(10.0, "CRORE_INR")
    assert norm_val == 100_000_000.0
    assert base_unit == "BASE_INR"

    # 50 Lakh = 5,000,000 INR
    norm_val, base_unit = normalize_numeric_value(50.0, "LAKH_INR")
    assert norm_val == 5_000_000.0
    assert base_unit == "BASE_INR"

    # 5 Years = 1825 Days
    norm_val, base_unit = normalize_numeric_value(5.0, "YEARS")
    assert norm_val == 5 * 365.0
    assert base_unit == "BASE_DAYS"


def test_numeric_threshold_evaluation_all_operators():
    """Verify >=, >, <=, <, = numeric threshold evaluations."""
    # 1. >= PASS & FAIL
    rule_gte = _build_rule(
        ComplianceRuleType.NUMERIC_THRESHOLD,
        {"field": "annual_turnover", "operator": ">=", "expected_value": 10.0, "unit": "CRORE_INR"},
    )
    # Pass: 12 Crore >= 10 Crore
    status, actual, expected, _, exp = evaluate_single_rule(
        rule_gte, {"financial": {"annual_turnover": {"value": 12.0, "unit": "CRORE_INR"}}}
    )
    assert status == EvaluationStatus.PASS
    assert "satisfies requirement" in exp

    # Fail: 8 Crore >= 10 Crore
    status, actual, expected, _, exp = evaluate_single_rule(
        rule_gte, {"financial": {"annual_turnover": {"value": 8.0, "unit": "CRORE_INR"}}}
    )
    assert status == EvaluationStatus.FAIL
    assert "fails to satisfy requirement" in exp

    # 2. Cross-unit normalization: 1000 Lakhs == 10 Crores -> PASS
    status, actual, expected, _, _ = evaluate_single_rule(
        rule_gte, {"financial": {"annual_turnover": {"value": 1000.0, "unit": "LAKH_INR"}}}
    )
    assert status == EvaluationStatus.PASS

    # 3. <= PASS & FAIL (e.g. delivery days <= 60)
    rule_lte = _build_rule(
        ComplianceRuleType.NUMERIC_THRESHOLD,
        {"field": "delivery_days", "operator": "<=", "expected_value": 60.0, "unit": "DAYS"},
    )
    status, _, _, _, _ = evaluate_single_rule(rule_lte, {"commercial": {"delivery_days": 45.0}})
    assert status == EvaluationStatus.PASS

    status, _, _, _, _ = evaluate_single_rule(rule_lte, {"commercial": {"delivery_days": 90.0}})
    assert status == EvaluationStatus.FAIL

    # 4. Incompatible units -> NOT_VERIFIABLE
    status, _, _, _, exp = evaluate_single_rule(
        rule_gte, {"financial": {"annual_turnover": {"value": 10.0, "unit": "DAYS"}}}
    )
    assert status == EvaluationStatus.NOT_VERIFIABLE
    assert "Cannot safely compare incompatible units" in exp

    # 5. Missing numeric evidence -> NOT_VERIFIABLE
    status, _, _, _, exp = evaluate_single_rule(rule_gte, {"financial": {}})
    assert status == EvaluationStatus.NOT_VERIFIABLE
    assert "No evidence provided" in exp


def test_numeric_range_evaluation():
    """Verify NUMERIC_RANGE evaluations."""
    rule_range = _build_rule(
        ComplianceRuleType.NUMERIC_RANGE,
        {"field": "batch_quantity", "min": 100.0, "max": 500.0, "unit": "UNITS"},
    )

    # Within range -> PASS
    status, _, _, _, _ = evaluate_single_rule(rule_range, {"batch_quantity": 250.0})
    assert status == EvaluationStatus.PASS

    # Outside range -> FAIL
    status, _, _, _, _ = evaluate_single_rule(rule_range, {"batch_quantity": 600.0})
    assert status == EvaluationStatus.FAIL

    # Missing -> NOT_VERIFIABLE
    status, _, _, _, _ = evaluate_single_rule(rule_range, {})
    assert status == EvaluationStatus.NOT_VERIFIABLE


def test_required_document_evaluation():
    """Verify document presence, alternate document, known absence, and unknown evidence."""
    rule_doc = _build_rule(
        ComplianceRuleType.REQUIRED_DOCUMENT,
        {"document_type": "GST_CERTIFICATE", "alternate_documents": ["PROVISIONAL_GST"]},
    )

    # Case A: Document information is absent from evidence payload -> NOT_VERIFIABLE
    status, _, _, _, exp = evaluate_single_rule(rule_doc, {"bidder_profile": {}})
    assert status == EvaluationStatus.NOT_VERIFIABLE
    assert "No document submission list was provided" in exp

    # Case B: Document list is provided, but required document is absent -> FAIL
    status, _, _, _, exp = evaluate_single_rule(rule_doc, {"documents": ["PAN_CARD", "INCORPORATION_CERTIFICATE"]})
    assert status == EvaluationStatus.FAIL
    assert "absent from bidder submission bundle" in exp

    # Case C: Primary document is present -> PASS
    status, _, _, _, exp = evaluate_single_rule(rule_doc, {"documents": ["PAN_CARD", "GST_CERTIFICATE"]})
    assert status == EvaluationStatus.PASS
    assert "confirmed present" in exp

    # Case D: Alternate document is present -> PASS
    status, _, _, _, exp = evaluate_single_rule(rule_doc, {"documents": ["PROVISIONAL_GST"]})
    assert status == EvaluationStatus.PASS
    assert "Accepted alternate document" in exp


def test_boolean_requirement_evaluation():
    """Verify BOOLEAN_REQUIREMENT evaluations."""
    rule_bool = _build_rule(
        ComplianceRuleType.BOOLEAN_REQUIREMENT,
        {"field": "non_blacklisted", "expected": True},
    )

    # True expected & True actual -> PASS
    status, _, _, _, _ = evaluate_single_rule(rule_bool, {"declarations": {"non_blacklisted": True}})
    assert status == EvaluationStatus.PASS

    # True expected & False actual -> FAIL
    status, _, _, _, _ = evaluate_single_rule(rule_bool, {"declarations": {"non_blacklisted": False}})
    assert status == EvaluationStatus.FAIL

    # Missing declaration -> NOT_VERIFIABLE
    status, _, _, _, _ = evaluate_single_rule(rule_bool, {"declarations": {}})
    assert status == EvaluationStatus.NOT_VERIFIABLE


def test_existence_check_evaluation():
    """Verify EXISTENCE_CHECK evaluations."""
    rule_exist = _build_rule(
        ComplianceRuleType.EXISTENCE_CHECK,
        {"field": "gst_registration_number"},
    )

    # Populated string -> PASS
    status, _, _, _, _ = evaluate_single_rule(
        rule_exist, {"attributes": {"gst_registration_number": "27AAPFU0939F1ZV"}}
    )
    assert status == EvaluationStatus.PASS

    # Empty string -> FAIL
    status, _, _, _, _ = evaluate_single_rule(
        rule_exist, {"attributes": {"gst_registration_number": ""}}
    )
    assert status == EvaluationStatus.FAIL

    # Missing attributes payload -> NOT_VERIFIABLE
    status, _, _, _, _ = evaluate_single_rule(rule_exist, {})
    assert status == EvaluationStatus.NOT_VERIFIABLE


def test_applicability_gate():
    """Verify applicability filtering: inapplicable requirements yield NOT_APPLICABLE (never PASS)."""
    rule_oem = _build_rule(
        ComplianceRuleType.REQUIRED_DOCUMENT,
        {"document_type": "OEM_AUTHORIZATION"},
        applicability=RequirementApplicability.OEM,
    )

    # Bidder is OEM -> evaluates requirement (and passes if doc present)
    status, _, _, _, _ = evaluate_single_rule(
        rule_oem,
        {"bidder_profile": {"bidder_type": "OEM"}, "documents": ["OEM_AUTHORIZATION"]},
    )
    assert status == EvaluationStatus.PASS

    # Bidder is STARTUP (not OEM) -> NOT_APPLICABLE (does NOT evaluate as PASS or FAIL)
    status, _, _, _, exp = evaluate_single_rule(
        rule_oem,
        {"bidder_profile": {"bidder_type": "STARTUP"}, "documents": []},
    )
    assert status == EvaluationStatus.NOT_APPLICABLE
    assert "Requirement applies strictly to OEMs" in exp


def test_date_limit_evaluation():
    """Verify DATE_LIMIT deadline comparisons."""
    rule_date = _build_rule(
        ComplianceRuleType.DATE_LIMIT,
        {"field": "submission_date", "reference": "submission_deadline", "operator": "<="},
    )

    # Submission before deadline -> PASS
    status, _, _, _, _ = evaluate_single_rule(
        rule_date,
        {"dates": {"submission_date": "2026-09-10T10:00:00Z", "submission_deadline": "2026-09-15T17:00:00Z"}},
    )
    assert status == EvaluationStatus.PASS

    # Submission after deadline -> FAIL
    status, _, _, _, _ = evaluate_single_rule(
        rule_date,
        {"dates": {"submission_date": "2026-09-16T10:00:00Z", "submission_deadline": "2026-09-15T17:00:00Z"}},
    )
    assert status == EvaluationStatus.FAIL

    # Missing date -> NOT_VERIFIABLE
    status, _, _, _, _ = evaluate_single_rule(rule_date, {"dates": {}})
    assert status == EvaluationStatus.NOT_VERIFIABLE


def test_unsupported_rule_evaluation():
    """Verify UNSUPPORTED rules return NOT_VERIFIABLE with clear diagnostic message."""
    rule_unsupported = _build_rule(
        ComplianceRuleType.UNSUPPORTED,
        {"reason": "Narrative requirement without deterministic rules"},
    )
    status, _, _, _, exp = evaluate_single_rule(rule_unsupported, {"financial": {"annual_turnover": 100.0}})
    assert status == EvaluationStatus.NOT_VERIFIABLE
    assert "could not be converted into a deterministic compliance rule" in exp
