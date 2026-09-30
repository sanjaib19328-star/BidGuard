import uuid
import pytest

from app.models.enums import (
    ClauseCategory,
    ComplianceRuleType,
    RequirementApplicability,
    RequirementOperator,
    RequirementType,
    RiskHint,
    VerificationMethod,
)
from app.models.requirement import TenderRequirement
from app.services.compliance_rule_compiler import (
    compile_requirement_to_rule,
    infer_field_name,
    infer_document_type,
    infer_boolean_field,
)


def _build_dummy_req(
    description: str,
    category: ClauseCategory = ClauseCategory.FINANCIAL,
    req_type: RequirementType = RequirementType.MIN_TURNOVER,
    val_num: float = None,
    unit: str = None,
    op: str = None,
    required_evidence: list = None,
    applicability: RequirementApplicability = RequirementApplicability.ALL_BIDDERS,
    app_cond: str = None,
) -> TenderRequirement:
    return TenderRequirement(
        id=uuid.uuid4(),
        tender_id=uuid.uuid4(),
        clause_id=uuid.uuid4(),
        category=category,
        requirement_type=req_type,
        description=description,
        operator=op,
        value_numeric=val_num,
        unit=unit,
        required_evidence=required_evidence or [],
        verification_method=VerificationMethod.RULE if val_num else VerificationMethod.DOCUMENT,
        risk_hint=RiskHint.MEDIUM,
        applicability=applicability,
        applicability_condition=app_cond,
        mandatory=True,
    )


def test_compile_numeric_threshold_rule():
    """Verify compiling a financial numeric threshold requirement."""
    req = _build_dummy_req(
        description="Average annual turnover of at least ₹10 crore during last 3 years.",
        category=ClauseCategory.FINANCIAL,
        req_type=RequirementType.MIN_TURNOVER,
        val_num=10.0,
        unit="CRORE_INR",
        op=">=",
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.NUMERIC_THRESHOLD
    assert config["expected_value"] == 10.0
    assert config["unit"] == "CRORE_INR"
    assert config["operator"] == ">="
    assert config["field"] == "annual_turnover"
    assert "Verify annual_turnover >= 10.0 CRORE_INR" in desc


def test_compile_numeric_range_rule():
    """Verify compiling a requirement specifying a numeric range."""
    req = _build_dummy_req(
        description="Delivery batch quantity between 100 and 500 units per shipment.",
        category=ClauseCategory.COMMERCIAL,
        req_type=RequirementType.OTHER,
        val_num=100.0,
        unit="UNITS",
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.NUMERIC_RANGE
    assert config["min"] == 100.0
    assert config["max"] == 500.0
    assert config["unit"] == "UNITS"


def test_compile_required_document_rule():
    """Verify compiling statutory/technical document requirements."""
    req = _build_dummy_req(
        description="Bidder must submit a valid copy of GST registration certificate.",
        category=ClauseCategory.STATUTORY,
        req_type=RequirementType.GST_REGISTRATION,
        required_evidence=["GST_CERTIFICATE"],
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.REQUIRED_DOCUMENT
    assert config["document_type"] == "GST_CERTIFICATE"
    assert "GST_CERTIFICATE" in desc


def test_compile_boolean_requirement_rule():
    """Verify compiling declarations such as non-blacklisting."""
    req = _build_dummy_req(
        description="The bidder must submit declaration confirming they are not blacklisted by any Government agency.",
        category=ClauseCategory.ELIGIBILITY,
        req_type=RequirementType.DECLARATION_REQUIRED,
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.BOOLEAN_REQUIREMENT
    assert config["field"] == "non_blacklisted"
    assert config["expected"] is True


def test_compile_existence_check_rule():
    """Verify compiling identifier existence criteria (e.g. GSTIN / PAN)."""
    req = _build_dummy_req(
        description="Bidder must possess a valid GSTIN and provide the registration number.",
        category=ClauseCategory.STATUTORY,
        req_type=RequirementType.STATUTORY_LICENSE,
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.EXISTENCE_CHECK
    assert config["field"] == "gst_registration_number"


def test_compile_conditional_rule():
    """Verify compiling conditional clauses into structured CONDITIONAL_RULE."""
    req = _build_dummy_req(
        description="OEM authorization certificate is strictly required if the bidder is an authorized dealer.",
        category=ClauseCategory.ELIGIBILITY,
        req_type=RequirementType.OEM_AUTHORIZATION,
        required_evidence=["OEM_AUTHORIZATION"],
        applicability=RequirementApplicability.CONDITIONAL,
        app_cond="if the bidder is an authorized dealer",
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.CONDITIONAL_RULE
    assert config["condition"]["applicability"] == "CONDITIONAL"
    assert "then_rule" in config
    assert config["then_rule"]["rule_type"] == "REQUIRED_DOCUMENT"
    assert config["then_rule"]["configuration"]["document_type"] == "OEM_AUTHORIZATION"


def test_compile_unsupported_narrative_rule():
    """Verify vague narrative clauses produce an explicit UNSUPPORTED rule rather than inventing fake logic."""
    req = _build_dummy_req(
        description="Bidder should enjoy strong market reputation and goodwill among customers.",
        category=ClauseCategory.GENERAL,
        req_type=RequirementType.OTHER,
    )
    rule_type, config, desc = compile_requirement_to_rule(req)

    assert rule_type == ComplianceRuleType.UNSUPPORTED
    assert "could not be converted into a deterministic compliance rule" in config["reason"]
