import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.compliance_evaluation import ComplianceEvaluation
from app.models.compliance_rule import ComplianceRule
from app.models.enums import (
    ComplianceRuleType,
    EvaluationStatus,
    RequirementApplicability,
)
from app.models.requirement import TenderRequirement
from app.services.audit_service import log_audit_event
from app.services.document_service import get_tender_by_id


# ==============================================================================
# 1. Unit Normalization & Helper Math
# ==============================================================================

# Conversion factors to base units (INR for currency, DAYS for time)
CURRENCY_TO_BASE_INR = {
    "INR": 1.0,
    "LAKH_INR": 100_000.0,
    "CRORE_INR": 10_000_000.0,
}

TIME_TO_BASE_DAYS = {
    "DAYS": 1.0,
    "MONTHS": 30.0,
    "YEARS": 365.0,
}


def normalize_numeric_value(val: float, unit: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    """Convert scalar values into standard base units for safe comparison."""
    if unit is None:
        return val, "SCALAR"

    u = unit.upper()
    if u in CURRENCY_TO_BASE_INR:
        return val * CURRENCY_TO_BASE_INR[u], "BASE_INR"
    if u in TIME_TO_BASE_DAYS:
        return val * TIME_TO_BASE_DAYS[u], "BASE_DAYS"
    if u in {"PERCENT", "PROJECTS", "UNITS"}:
        return val, u

    return val, u


# ==============================================================================
# 2. Rule Evaluation Engine Functions
# ==============================================================================

def check_applicability(
    applicability: RequirementApplicability,
    bidder_profile: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """Verify whether a requirement applies to this bidder profile.
    
    Returns:
        (is_applicable, inapplicability_reason)
    """
    if applicability == RequirementApplicability.ALL_BIDDERS:
        return True, None

    b_type = (bidder_profile.get("bidder_type") or "UNKNOWN").upper()
    is_msme = bool(bidder_profile.get("is_msme", False))
    is_startup = bool(bidder_profile.get("is_startup", False))

    if applicability == RequirementApplicability.OEM:
        if b_type != "OEM":
            return False, f"Requirement applies strictly to OEMs. Evaluated bidder is '{b_type}'."
        return True, None

    if applicability == RequirementApplicability.AUTHORIZED_DEALER:
        if b_type not in {"AUTHORIZED_DEALER", "OEM"}:
            return False, f"Requirement applies to Authorized Dealers. Evaluated bidder is '{b_type}'."
        return True, None

    if applicability == RequirementApplicability.MSME:
        if not is_msme:
            return False, "Requirement applies exclusively to MSME entities."
        return True, None

    if applicability == RequirementApplicability.STARTUP:
        if not is_startup:
            return False, "Requirement applies exclusively to recognized Startups."
        return True, None

    if applicability == RequirementApplicability.FOREIGN_BIDDER:
        country = (bidder_profile.get("country") or "IN").upper()
        if country == "IN":
            return False, "Requirement applies exclusively to Foreign Bidders."
        return True, None

    return True, None


def evaluate_numeric_threshold(
    config: Dict[str, Any],
    evidence: Dict[str, Any],
    clause_ref: Optional[str] = None,
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate NUMERIC_THRESHOLD rule against financial or scalar evidence."""
    field_name = config.get("field", "annual_turnover")
    expected_val = config.get("expected_value")
    expected_unit = config.get("unit")
    operator_str = config.get("operator", ">=")

    expected_display = f"{operator_str} {expected_val} {expected_unit or ''}".strip()

    # Locate actual value in evidence
    actual_data = None
    for section in ["financial", "commercial", "experience", "attributes", "dates"]:
        if section in evidence and isinstance(evidence[section], dict) and field_name in evidence[section]:
            actual_data = evidence[section][field_name]
            break
    if actual_data is None and field_name in evidence:
        actual_data = evidence[field_name]

    if actual_data is None:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            field_name,
            f"No evidence provided for required numeric field '{field_name}'.",
        )

    # Parse actual scalar and unit
    if isinstance(actual_data, dict):
        actual_val = actual_data.get("value")
        actual_unit = actual_data.get("unit", expected_unit)
    else:
        try:
            actual_val = float(actual_data)
            actual_unit = expected_unit
        except (ValueError, TypeError):
            return (
                EvaluationStatus.NOT_VERIFIABLE,
                str(actual_data),
                expected_display,
                field_name,
                f"Evidence value for '{field_name}' could not be parsed as a numeric scalar: {actual_data}",
            )

    if actual_val is None:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            field_name,
            f"Actual value for '{field_name}' is missing.",
        )

    actual_display = f"{actual_val} {actual_unit or ''}".strip()

    # Normalize units
    norm_expected, base_expected_unit = normalize_numeric_value(expected_val, expected_unit)
    norm_actual, base_actual_unit = normalize_numeric_value(actual_val, actual_unit)

    if base_expected_unit != base_actual_unit:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            actual_display,
            expected_display,
            field_name,
            f"Cannot safely compare incompatible units: expected '{expected_unit}', actual '{actual_unit}'.",
        )

    # Operator evaluation
    passed = False
    if operator_str in {">=", "GTE"}:
        passed = norm_actual >= norm_expected
    elif operator_str in {">", "GT"}:
        passed = norm_actual > norm_expected
    elif operator_str in {"<=", "LTE"}:
        passed = norm_actual <= norm_expected
    elif operator_str in {"<", "LT"}:
        passed = norm_actual < norm_expected
    elif operator_str in {"=", "==", "EQ"}:
        passed = abs(norm_actual - norm_expected) < 1e-6
    else:
        passed = norm_actual >= norm_expected

    clause_info = f" ({clause_ref})" if clause_ref else ""
    if passed:
        return (
            EvaluationStatus.PASS,
            actual_display,
            expected_display,
            field_name,
            f"Bidder value {actual_display} satisfies requirement {expected_display}{clause_info}.",
        )
    else:
        return (
            EvaluationStatus.FAIL,
            actual_display,
            expected_display,
            field_name,
            f"Bidder value {actual_display} fails to satisfy requirement {expected_display}{clause_info}.",
        )


def evaluate_numeric_range(
    config: Dict[str, Any],
    evidence: Dict[str, Any],
    clause_ref: Optional[str] = None,
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate NUMERIC_RANGE rule."""
    field_name = config.get("field", "generic_numeric")
    min_val = config.get("min")
    max_val = config.get("max")
    unit = config.get("unit")

    expected_display = f"Between {min_val} and {max_val} {unit or ''}".strip()

    actual_data = None
    for section in ["financial", "commercial", "experience", "attributes", "dates"]:
        if section in evidence and isinstance(evidence[section], dict) and field_name in evidence[section]:
            actual_data = evidence[section][field_name]
            break
    if actual_data is None and field_name in evidence:
        actual_data = evidence[field_name]

    if actual_data is None:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            field_name,
            f"No evidence provided for range requirement '{field_name}'.",
        )

    if isinstance(actual_data, dict):
        actual_val = actual_data.get("value")
        actual_unit = actual_data.get("unit", unit)
    else:
        try:
            actual_val = float(actual_data)
            actual_unit = unit
        except (ValueError, TypeError):
            return (
                EvaluationStatus.NOT_VERIFIABLE,
                str(actual_data),
                expected_display,
                field_name,
                f"Range value for '{field_name}' could not be parsed as float: {actual_data}",
            )

    actual_display = f"{actual_val} {actual_unit or ''}".strip()

    norm_min, _ = normalize_numeric_value(min_val, unit)
    norm_max, _ = normalize_numeric_value(max_val, unit)
    norm_actual, base_act = normalize_numeric_value(actual_val, actual_unit)

    clause_info = f" ({clause_ref})" if clause_ref else ""
    if norm_min <= norm_actual <= norm_max:
        return (
            EvaluationStatus.PASS,
            actual_display,
            expected_display,
            field_name,
            f"Bidder value {actual_display} falls within acceptable range {expected_display}{clause_info}.",
        )
    else:
        return (
            EvaluationStatus.FAIL,
            actual_display,
            expected_display,
            field_name,
            f"Bidder value {actual_display} falls outside acceptable range {expected_display}{clause_info}.",
        )


def evaluate_required_document(
    config: Dict[str, Any],
    evidence: Dict[str, Any],
    clause_ref: Optional[str] = None,
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate REQUIRED_DOCUMENT rule distinguishing missing evidence vs known absence."""
    target_doc = config.get("document_type", "SUPPORTING_DOCUMENT")
    alt_docs = config.get("alternate_documents") or []
    acceptable_docs = [target_doc] + alt_docs

    expected_display = f"Required Document: {target_doc}"

    # Case A: Document submission information is entirely missing from evidence payload
    if "documents" not in evidence:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            "documents",
            "No document submission list was provided in the evidence payload.",
        )

    submitted_docs = evidence.get("documents")
    if not isinstance(submitted_docs, list):
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            str(submitted_docs),
            expected_display,
            "documents",
            "Evidence 'documents' must be a list of document type strings.",
        )

    norm_submitted = {d.upper().strip() for d in submitted_docs}

    # Case C: Primary document is present
    clause_info = f" ({clause_ref})" if clause_ref else ""
    if target_doc.upper() in norm_submitted:
        return (
            EvaluationStatus.PASS,
            target_doc,
            expected_display,
            f"documents.{target_doc}",
            f"Required document '{target_doc}' is confirmed present in submission bundle{clause_info}.",
        )

    # Check alternate documents
    for alt in alt_docs:
        if alt.upper() in norm_submitted:
            return (
                EvaluationStatus.PASS,
                alt,
                expected_display,
                f"documents.{alt}",
                f"Accepted alternate document '{alt}' is confirmed present in submission bundle{clause_info}.",
            )

    # Check for PARTIAL if multiple documents were specified in configuration
    if alt_docs and any(d in norm_submitted for d in acceptable_docs):
        return (
            EvaluationStatus.PARTIAL,
            ", ".join(norm_submitted.intersection(set(acceptable_docs))),
            expected_display,
            "documents",
            f"Partially satisfied: Some alternate documents present, but primary document '{target_doc}' is missing{clause_info}.",
        )

    # Case B: We know the submission contains no such document
    return (
        EvaluationStatus.FAIL,
        f"Submitted: {', '.join(submitted_docs) if submitted_docs else 'None'}",
        expected_display,
        "documents",
        f"Required document '{target_doc}' is absent from bidder submission bundle{clause_info}.",
    )


def evaluate_boolean_requirement(
    config: Dict[str, Any],
    evidence: Dict[str, Any],
    clause_ref: Optional[str] = None,
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate BOOLEAN_REQUIREMENT rule against bidder declarations."""
    field_name = config.get("field", "declaration_accepted")
    expected_val = bool(config.get("expected", True))
    expected_display = f"{field_name} == {expected_val}"

    # Search in declarations or attributes
    actual_val = None
    if "declarations" in evidence and field_name in evidence["declarations"]:
        actual_val = evidence["declarations"][field_name]
    elif "attributes" in evidence and field_name in evidence["attributes"]:
        actual_val = evidence["attributes"][field_name]
    elif field_name in evidence:
        actual_val = evidence[field_name]

    if actual_val is None:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            f"declarations.{field_name}",
            f"No declaration or evidence provided for boolean requirement '{field_name}'.",
        )

    actual_bool = bool(actual_val)
    actual_display = f"{field_name} == {actual_bool}"
    clause_info = f" ({clause_ref})" if clause_ref else ""

    if actual_bool == expected_val:
        return (
            EvaluationStatus.PASS,
            str(actual_bool),
            str(expected_val),
            f"declarations.{field_name}",
            f"Bidder declaration satisfies requirement '{field_name} == {expected_val}'{clause_info}.",
        )
    else:
        return (
            EvaluationStatus.FAIL,
            str(actual_bool),
            str(expected_val),
            f"declarations.{field_name}",
            f"Bidder declaration '{field_name}' is {actual_bool}, expected {expected_val}{clause_info}.",
        )


def evaluate_existence_check(
    config: Dict[str, Any],
    evidence: Dict[str, Any],
    clause_ref: Optional[str] = None,
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate EXISTENCE_CHECK rule for required attribute numbers (GSTIN, PAN, etc.)."""
    field_name = config.get("field", "registration_number")
    expected_display = f"Non-empty {field_name}"

    attributes = evidence.get("attributes")
    if attributes is None and field_name not in evidence:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            f"attributes.{field_name}",
            f"No attributes payload provided in evidence to verify existence of '{field_name}'.",
        )

    actual_val = None
    if isinstance(attributes, dict) and field_name in attributes:
        actual_val = attributes[field_name]
    elif field_name in evidence:
        actual_val = evidence[field_name]

    clause_info = f" ({clause_ref})" if clause_ref else ""
    if actual_val and str(actual_val).strip():
        return (
            EvaluationStatus.PASS,
            str(actual_val).strip(),
            expected_display,
            f"attributes.{field_name}",
            f"Required identifier '{field_name}' exists and is populated: {actual_val}{clause_info}.",
        )
    else:
        return (
            EvaluationStatus.FAIL,
            "Missing or empty",
            expected_display,
            f"attributes.{field_name}",
            f"Required identifier '{field_name}' is missing or empty in bidder profile{clause_info}.",
        )


def evaluate_date_limit(
    config: Dict[str, Any],
    evidence: Dict[str, Any],
    clause_ref: Optional[str] = None,
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate DATE_LIMIT rule (e.g. submission timestamp before deadline)."""
    field_name = config.get("field", "submission_date")
    ref_field = config.get("reference", "submission_deadline")
    op_str = config.get("operator", "<=")

    dates = evidence.get("dates", {})
    sub_date_str = dates.get(field_name) or evidence.get(field_name)
    ref_date_str = dates.get(ref_field) or evidence.get(ref_field)

    expected_display = f"{field_name} {op_str} {ref_field}"

    if not sub_date_str:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            expected_display,
            f"dates.{field_name}",
            f"Submission timestamp '{field_name}' is missing from evidence.",
        )
    if not ref_date_str:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            str(sub_date_str),
            expected_display,
            f"dates.{ref_field}",
            f"Reference deadline '{ref_field}' is not defined in evidence.",
        )

    try:
        dt_actual = datetime.fromisoformat(str(sub_date_str).replace("Z", "+00:00"))
        dt_ref = datetime.fromisoformat(str(ref_date_str).replace("Z", "+00:00"))
    except Exception as e:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            str(sub_date_str),
            expected_display,
            "dates",
            f"Failed to parse dates as ISO timestamps: {e}",
        )

    passed = dt_actual <= dt_ref if op_str == "<=" else dt_actual >= dt_ref
    clause_info = f" ({clause_ref})" if clause_ref else ""

    if passed:
        return (
            EvaluationStatus.PASS,
            str(sub_date_str),
            expected_display,
            f"dates.{field_name}",
            f"Timestamp {sub_date_str} satisfies deadline condition {expected_display}{clause_info}.",
        )
    else:
        return (
            EvaluationStatus.FAIL,
            str(sub_date_str),
            expected_display,
            f"dates.{field_name}",
            f"Timestamp {sub_date_str} violates deadline condition {expected_display}{clause_info}.",
        )


def evaluate_single_rule(
    rule: ComplianceRule,
    evidence: Dict[str, Any],
) -> Tuple[EvaluationStatus, Optional[str], Optional[str], Optional[str], str]:
    """Evaluate an individual ComplianceRule against structured evidence.
    
    Returns:
        (status, actual_value, expected_value, evidence_reference, explanation)
    """
    req = rule.requirement
    clause_ref = None
    if req and req.clause:
        clause_ref = f"Clause {req.clause.clause_number}"

    # 1. Applicability Check First
    bidder_profile = evidence.get("bidder_profile", {})
    if req:
        is_app, inapp_reason = check_applicability(req.applicability, bidder_profile)
        if not is_app:
            return (
                EvaluationStatus.NOT_APPLICABLE,
                bidder_profile.get("bidder_type", "UNKNOWN"),
                req.applicability.value,
                "bidder_profile.bidder_type",
                inapp_reason or "Requirement is not applicable to this bidder class.",
            )

    # 2. Rule Type Dispatch
    rtype = rule.rule_type
    config = rule.rule_configuration or {}

    if rtype == ComplianceRuleType.NUMERIC_THRESHOLD:
        return evaluate_numeric_threshold(config, evidence, clause_ref)

    if rtype == ComplianceRuleType.NUMERIC_RANGE:
        return evaluate_numeric_range(config, evidence, clause_ref)

    if rtype == ComplianceRuleType.REQUIRED_DOCUMENT:
        return evaluate_required_document(config, evidence, clause_ref)

    if rtype == ComplianceRuleType.BOOLEAN_REQUIREMENT:
        return evaluate_boolean_requirement(config, evidence, clause_ref)

    if rtype == ComplianceRuleType.EXISTENCE_CHECK:
        return evaluate_existence_check(config, evidence, clause_ref)

    if rtype == ComplianceRuleType.DATE_LIMIT:
        return evaluate_date_limit(config, evidence, clause_ref)

    if rtype == ComplianceRuleType.CONDITIONAL_RULE:
        then_rule = config.get("then_rule", {})
        sub_type = ComplianceRuleType(then_rule.get("rule_type", ComplianceRuleType.UNSUPPORTED.value))
        sub_config = then_rule.get("configuration", {})

        # Create proxy rule to evaluate consequent
        sub_rule = ComplianceRule(
            id=rule.id,
            tender_id=rule.tender_id,
            requirement_id=rule.requirement_id,
            rule_type=sub_type,
            rule_configuration=sub_config,
            description=rule.description,
        )
        sub_rule.requirement = rule.requirement
        return evaluate_single_rule(sub_rule, evidence)

    if rtype == ComplianceRuleType.UNSUPPORTED:
        return (
            EvaluationStatus.NOT_VERIFIABLE,
            None,
            "Deterministic Rule",
            None,
            "This requirement could not be converted into a deterministic compliance rule.",
        )

    return (
        EvaluationStatus.NOT_VERIFIABLE,
        None,
        "Unknown Rule",
        None,
        f"Rule type '{rtype}' is not yet supported for automated evaluation.",
    )


# ==============================================================================
# 3. Main Evaluation Service Execution
# ==============================================================================

async def evaluate_tender_rules(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    evidence: Dict[str, Any],
    bidder_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[uuid.UUID, Dict[str, int], List[ComplianceEvaluation]]:
    """Execute deterministic evaluation for all enabled rules on a tender.
    
    Persists evaluation records with a unique evaluation_run_id for historical audit.
    
    Returns:
        (evaluation_run_id, summary_dict, evaluation_entities)
    """
    # 1. Tenant verification
    await get_tender_by_id(session, tender_id, organization_id)

    # 2. Retrieve enabled rules
    rule_stmt = (
        select(ComplianceRule)
        .options(
            selectinload(ComplianceRule.requirement).selectinload(TenderRequirement.clause),
        )
        .where(
            ComplianceRule.tender_id == tender_id,
            ComplianceRule.enabled == True,
        )
        .order_by(ComplianceRule.sequence_order.asc())
    )
    rule_res = await session.execute(rule_stmt)
    rules = list(rule_res.scalars().all())

    if not rules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender has no compiled compliance rules. Please compile rules first.",
        )

    # 3. Run evaluation
    run_id = uuid.uuid4()
    now_utc = datetime.now(timezone.utc)
    eval_entities: List[ComplianceEvaluation] = []

    summary = {
        "total": len(rules),
        "passed": 0,
        "failed": 0,
        "partial": 0,
        "not_verifiable": 0,
        "not_applicable": 0,
    }

    for rule in rules:
        status_enum, actual_val, expected_val, ev_ref, explanation = evaluate_single_rule(rule, evidence)

        # Update summary counts
        if status_enum == EvaluationStatus.PASS:
            summary["passed"] += 1
        elif status_enum == EvaluationStatus.FAIL:
            summary["failed"] += 1
        elif status_enum == EvaluationStatus.PARTIAL:
            summary["partial"] += 1
        elif status_enum == EvaluationStatus.NOT_VERIFIABLE:
            summary["not_verifiable"] += 1
        elif status_enum == EvaluationStatus.NOT_APPLICABLE:
            summary["not_applicable"] += 1

        eval_obj = ComplianceEvaluation(
            id=uuid.uuid4(),
            evaluation_run_id=run_id,
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=rule.requirement_id,
            rule_id=rule.id,
            status=status_enum,
            actual_value=actual_val,
            expected_value=expected_val,
            evidence_reference=ev_ref,
            explanation=explanation,
            evaluated_at=now_utc,
            evaluator_type="DETERMINISTIC_ENGINE",
            meta_data={
                "mandatory": rule.requirement.mandatory if rule.requirement else None,
                "risk_hint": rule.requirement.risk_hint.value if rule.requirement else None,
                "rule_type": rule.rule_type.value,
            },
        )
        eval_obj.rule = rule
        eval_obj.requirement = rule.requirement
        session.add(eval_obj)
        eval_entities.append(eval_obj)

    await session.flush()

    # 4. Audit Logging
    await log_audit_event(
        session=session,
        action="COMPLIANCE_EVALUATION_COMPLETED",
        entity_type="tender",
        entity_id=str(tender_id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state={
            "tender_id": str(tender_id),
            "evaluation_run_id": str(run_id),
            "bidder_id": bidder_id,
            "rules_evaluated": len(rules),
            "summary": summary,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()

    # Re-query with eager loading to prevent MissingGreenlet in API response formatting
    eval_stmt = (
        select(ComplianceEvaluation)
        .options(
            selectinload(ComplianceEvaluation.rule),
            selectinload(ComplianceEvaluation.requirement).selectinload(TenderRequirement.clause),
        )
        .where(ComplianceEvaluation.evaluation_run_id == run_id)
        .order_by(ComplianceEvaluation.created_at.asc())
    )
    eval_res = await session.execute(eval_stmt)
    loaded_entities = list(eval_res.scalars().all())

    return run_id, summary, loaded_entities


async def list_tender_evaluations(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    evaluation_run_id: Optional[uuid.UUID] = None,
    bidder_id: Optional[str] = None,
    status_filter: Optional[EvaluationStatus] = None,
) -> Tuple[List[ComplianceEvaluation], Dict[str, int]]:
    """List evaluations for a tender, optionally filtered by run ID or bidder ID."""
    await get_tender_by_id(session, tender_id, organization_id)

    query = (
        select(ComplianceEvaluation)
        .options(
            selectinload(ComplianceEvaluation.rule),
            selectinload(ComplianceEvaluation.requirement).selectinload(TenderRequirement.clause),
        )
        .where(ComplianceEvaluation.tender_id == tender_id)
    )

    if evaluation_run_id:
        query = query.where(ComplianceEvaluation.evaluation_run_id == evaluation_run_id)
    if bidder_id:
        query = query.where(ComplianceEvaluation.bidder_id == bidder_id)
    if status_filter:
        query = query.where(ComplianceEvaluation.status == status_filter)

    query = query.order_by(ComplianceEvaluation.evaluated_at.desc())
    res = await session.execute(query)
    items = list(res.scalars().all())

    summary = {
        "total": len(items),
        "passed": sum(1 for i in items if i.status == EvaluationStatus.PASS),
        "failed": sum(1 for i in items if i.status == EvaluationStatus.FAIL),
        "partial": sum(1 for i in items if i.status == EvaluationStatus.PARTIAL),
        "not_verifiable": sum(1 for i in items if i.status == EvaluationStatus.NOT_VERIFIABLE),
        "not_applicable": sum(1 for i in items if i.status == EvaluationStatus.NOT_APPLICABLE),
    }

    return items, summary
