import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.clause import TenderClause
from app.models.compliance_rule import ComplianceRule
from app.models.enums import (
    ClauseCategory,
    ComplianceRuleType,
    RequirementApplicability,
    RequirementType,
    VerificationMethod,
)
from app.models.requirement import TenderRequirement
from app.services.audit_service import log_audit_event
from app.services.document_service import get_tender_by_id


# ==============================================================================
# 1. Field Name Inference Helpers
# ==============================================================================

def infer_field_name(req: TenderRequirement) -> str:
    """Infer the canonical structured evidence field name for a requirement."""
    desc = req.description.lower()
    req_type_str = req.requirement_type.value if hasattr(req.requirement_type, "value") else str(req.requirement_type)

    if req.category == ClauseCategory.FINANCIAL or "turnover" in desc or "turnover" in req_type_str.lower():
        if "net worth" in desc or "net_worth" in req_type_str.lower():
            return "net_worth"
        if "solvency" in desc:
            return "solvency"
        if "emd" in desc or "earnest" in desc or "emd" in req_type_str.lower():
            return "emd_amount"
        if "pbg" in desc or "performance" in desc:
            return "performance_security_amount"
        return "annual_turnover"

    if "experience" in desc or "experience" in req_type_str.lower():
        if req.unit == "PROJECTS" or "similar" in desc or "works" in desc:
            return "similar_projects"
        return "years_of_experience"

    if req.category == ClauseCategory.COMMERCIAL:
        if "delivery" in desc or req.unit == "DAYS":
            return "delivery_days"
        if "validity" in desc:
            return "bid_validity_days"
        if "warranty" in desc:
            return "warranty_months"
        return "commercial_parameter"

    if req.category == ClauseCategory.TECHNICAL:
        return "technical_capacity"

    return "generic_numeric"


def infer_document_type(req: TenderRequirement) -> str:
    """Infer the primary document type expected for a requirement."""
    if req.required_evidence and len(req.required_evidence) > 0:
        return req.required_evidence[0]

    desc = req.description.lower()
    req_type_str = req.requirement_type.value if hasattr(req.requirement_type, "value") else str(req.requirement_type)

    if "gst" in desc or "gst" in req_type_str.lower():
        return "GST_CERTIFICATE"
    if "pan" in desc or "pan" in req_type_str.lower():
        return "PAN_CARD"
    if "oem" in desc or "maf" in desc or "authorization" in desc:
        return "OEM_AUTHORIZATION"
    if "iso" in desc:
        return "ISO_CERTIFICATE"
    if "audited" in desc or "balance sheet" in desc or "financial" in desc:
        return "AUDITED_FINANCIAL_STATEMENTS"
    if "turnover" in desc:
        return "CA_TURNOVER_CERTIFICATE"
    if "experience" in desc or "completion" in desc:
        return "EXPERIENCE_CERTIFICATE"
    if "incorporation" in desc or "registration" in desc:
        return "INCORPORATION_CERTIFICATE"
    if "integrity" in desc:
        return "INTEGRITY_PACT"
    if "affidavit" in desc:
        return "AFFIDAVIT"
    if "declaration" in desc or "blacklisted" in desc:
        return "NON_BLACKLISTING_DECLARATION"

    return "SUPPORTING_DOCUMENT"


def infer_boolean_field(req: TenderRequirement) -> str:
    """Infer the boolean evidence attribute key."""
    desc = req.description.lower()
    if "blacklist" in desc or "debar" in desc:
        return "non_blacklisted"
    if "gst" in desc:
        return "gst_registered"
    if "pan" in desc:
        return "pan_registered"
    if "msme" in desc:
        return "msme_registered"
    if "startup" in desc:
        return "startup_registered"
    if "integrity" in desc:
        return "integrity_pact_agreed"
    return "declaration_accepted"


def infer_attribute_field(req: TenderRequirement) -> str:
    """Infer the identifier attribute key for existence checks."""
    desc = req.description.lower()
    if "gst" in desc or "gstin" in desc:
        return "gst_registration_number"
    if "pan" in desc:
        return "pan_number"
    if "udyam" in desc or "msme" in desc:
        return "udyam_registration_number"
    if "cin" in desc or "incorporation" in desc:
        return "cin_number"
    return "registration_number"


# ==============================================================================
# 2. Rule Compiler Logic
# ==============================================================================

def compile_requirement_to_rule(req: TenderRequirement) -> Tuple[ComplianceRuleType, Dict[str, Any], str]:
    """Deterministically compile a TenderRequirement into executable rule parameters.
    
    Returns:
        (rule_type, rule_configuration, description)
    """
    desc = req.description.strip()
    norm_desc = desc.lower()

    # 1. Check for Conditional Applicability
    is_conditional = (
        req.applicability == RequirementApplicability.CONDITIONAL
        or bool(req.applicability_condition)
    )

    # 2. Financial / Numeric Threshold or Range
    if req.value_numeric is not None:
        field_name = infer_field_name(req)

        # Check for numeric range (e.g. "between X and Y", "100-500")
        range_match = re.search(r"\bbetween\s+([0-9.]+)\s+and\s+([0-9.]+)\b", norm_desc)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            inner_type = ComplianceRuleType.NUMERIC_RANGE
            inner_config = {
                "field": field_name,
                "min": min_val,
                "max": max_val,
                "unit": req.unit,
                "currency": req.currency,
                "period": req.period,
            }
            rule_desc = f"Verify {field_name} is between {min_val} and {max_val} {req.unit or ''}".strip()
        else:
            inner_type = ComplianceRuleType.NUMERIC_THRESHOLD
            op_str = req.operator or ">="
            inner_config = {
                "field": field_name,
                "operator": op_str,
                "expected_value": req.value_numeric,
                "unit": req.unit,
                "currency": req.currency,
                "period": req.period,
            }
            rule_desc = f"Verify {field_name} {op_str} {req.value_numeric} {req.unit or ''}".strip()

        if is_conditional:
            rule_type = ComplianceRuleType.CONDITIONAL_RULE
            rule_config = {
                "condition": {
                    "applicability": req.applicability.value,
                    "condition_text": req.applicability_condition,
                },
                "then_rule": {
                    "rule_type": inner_type.value,
                    "configuration": inner_config,
                },
            }
            return rule_type, rule_config, f"Conditional rule: {rule_desc} (Applies if: {req.applicability_condition or req.applicability.value})"
        return inner_type, inner_config, rule_desc

    # 3. Declarations & Boolean Criteria
    is_decl_type = (
        req.requirement_type in {RequirementType.DECLARATION_REQUIRED, RequirementType.AFFIDAVIT_REQUIRED}
        if hasattr(req, "requirement_type") else False
    )
    if is_decl_type or any(k in norm_desc for k in ["blacklist", "debar", "declaration", "affidavit"]):
        bool_field = infer_boolean_field(req)
        expected_bool = False if req.operator == "PROHIBITED" or "not be blacklisted" in norm_desc else True
        if "not be blacklisted" in norm_desc or "non-blacklist" in norm_desc or "not blacklisted" in norm_desc or "non_blacklisted" in norm_desc:
            expected_bool = True

        inner_type = ComplianceRuleType.BOOLEAN_REQUIREMENT
        inner_config = {
            "field": bool_field,
            "expected": expected_bool,
        }
        rule_desc = f"Verify boolean requirement: {bool_field} == {expected_bool}"
        return inner_type, inner_config, rule_desc

    # 4. Identifier Existence Checks
    if any(k in norm_desc for k in ["gstin", "pan number", "udyam number", "registration number"]):
        attr_field = infer_attribute_field(req)
        inner_type = ComplianceRuleType.EXISTENCE_CHECK
        inner_config = {
            "field": attr_field,
        }
        rule_desc = f"Verify presence of non-empty identifier: {attr_field}"
        return inner_type, inner_config, rule_desc

    # 5. Deadlines & Date Limits
    if any(k in norm_desc for k in ["deadline", "closing date", "expiry date", "before date"]):
        inner_type = ComplianceRuleType.DATE_LIMIT
        inner_config = {
            "operator": "<=",
            "field": "submission_date",
            "reference": "submission_deadline",
        }
        rule_desc = "Verify submission timestamp does not exceed tender deadline"
        return inner_type, inner_config, rule_desc

    # 6. Document Requirements
    has_evidence = bool(req.required_evidence and len(req.required_evidence) > 0)
    has_doc_keywords = any(k in norm_desc for k in ["certificate", "license", "authorization", "document", "copy of", "proof of"])

    if has_evidence or has_doc_keywords:
        doc_type = infer_document_type(req)
        alt_docs = [d for d in req.required_evidence if d != doc_type] if req.required_evidence else []
        inner_type = ComplianceRuleType.REQUIRED_DOCUMENT
        inner_config = {
            "document_type": doc_type,
            "alternate_documents": alt_docs,
        }
        rule_desc = f"Verify submission of required document: {doc_type}"

        if is_conditional:
            rule_type = ComplianceRuleType.CONDITIONAL_RULE
            rule_config = {
                "condition": {
                    "applicability": req.applicability.value,
                    "condition_text": req.applicability_condition,
                },
                "then_rule": {
                    "rule_type": inner_type.value,
                    "configuration": inner_config,
                },
            }
            return rule_type, rule_config, f"Conditional rule: {rule_desc} (Applies if: {req.applicability_condition or req.applicability.value})"
        return inner_type, inner_config, rule_desc

    # 7. Unsupported / Vague Narrative (Safe handling: never invent fake logic)
    rule_type = ComplianceRuleType.UNSUPPORTED
    rule_config = {
        "reason": "This requirement could not be converted into a deterministic compliance rule.",
        "description": desc,
    }
    rule_desc = f"Unsupported deterministic evaluation: {desc[:100]}"
    return rule_type, rule_config, rule_desc


# ==============================================================================
# 3. Rule Compilation Service
# ==============================================================================

async def compile_tender_rules(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    force_recompile: bool = False,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[List[ComplianceRule], int, int, int, Dict[str, int]]:
    """Compile structured requirements into executable compliance rules.
    
    Safe Re-compilation:
        - If rules exist and force_recompile is False, returns existing set.
        - If force_recompile is True, updates existing rules by requirement_id and adds new ones
          WITHOUT deleting historical ComplianceEvaluation records.
    
    Returns:
        (rules, rules_created, rules_updated, rules_reused, rules_by_type)
    """
    # 1. Tenant verification
    await get_tender_by_id(session, tender_id, organization_id)

    # 2. Retrieve existing rules
    rule_stmt = (
        select(ComplianceRule)
        .options(selectinload(ComplianceRule.requirement))
        .where(ComplianceRule.tender_id == tender_id)
        .order_by(ComplianceRule.sequence_order.asc())
    )
    existing_rules_res = await session.execute(rule_stmt)
    existing_rules = list(existing_rules_res.scalars().all())

    # Map existing rules by requirement_id
    existing_by_req: Dict[uuid.UUID, ComplianceRule] = {
        r.requirement_id: r for r in existing_rules
    }

    if existing_rules and not force_recompile:
        type_breakdown: Dict[str, int] = {}
        for r in existing_rules:
            type_breakdown[r.rule_type.value] = type_breakdown.get(r.rule_type.value, 0) + 1
        return existing_rules, 0, 0, len(existing_rules), type_breakdown

    # 3. Retrieve requirements for this tender
    req_stmt = (
        select(TenderRequirement)
        .options(selectinload(TenderRequirement.clause))
        .where(TenderRequirement.tender_id == tender_id)
        .order_by(TenderRequirement.sequence_order.asc())
    )
    req_res = await session.execute(req_stmt)
    requirements = list(req_res.scalars().all())

    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender has no extracted requirements yet. Please run requirement extraction first.",
        )

    # 4. Compile rules
    created_count = 0
    updated_count = 0
    reused_count = 0
    final_rules: List[ComplianceRule] = []
    type_breakdown: Dict[str, int] = {}

    for req in requirements:
        rule_type, rule_config, rule_desc = compile_requirement_to_rule(req)

        if req.id in existing_by_req:
            # Update existing rule in-place (preserves rule ID and historical evaluation records!)
            rule = existing_by_req[req.id]
            rule.rule_type = rule_type
            rule.rule_configuration = rule_config
            rule.description = rule_desc
            rule.sequence_order = req.sequence_order
            rule.confidence = req.confidence
            rule.enabled = True
            updated_count += 1
            final_rules.append(rule)
        else:
            # Create new rule
            new_rule = ComplianceRule(
                id=uuid.uuid4(),
                tender_id=tender_id,
                requirement_id=req.id,
                rule_type=rule_type,
                rule_configuration=rule_config,
                description=rule_desc,
                enabled=True,
                sequence_order=req.sequence_order,
                confidence=req.confidence,
            )
            session.add(new_rule)
            created_count += 1
            final_rules.append(new_rule)

        type_key = rule_type.value
        type_breakdown[type_key] = type_breakdown.get(type_key, 0) + 1

    await session.flush()

    # 5. Audit Logging
    await log_audit_event(
        session=session,
        action="COMPLIANCE_RULES_COMPILED",
        entity_type="tender",
        entity_id=str(tender_id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state={
            "tender_id": str(tender_id),
            "rules_total": len(final_rules),
            "rules_created": created_count,
            "rules_updated": updated_count,
            "rules_reused": reused_count,
            "force_recompile": force_recompile,
            "types_breakdown": type_breakdown,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()

    reloaded_stmt = (
        select(ComplianceRule)
        .options(
            selectinload(ComplianceRule.requirement).selectinload(TenderRequirement.clause),
        )
        .where(ComplianceRule.tender_id == tender_id)
        .order_by(ComplianceRule.sequence_order.asc())
    )
    reloaded_res = await session.execute(reloaded_stmt)
    loaded_rules = list(reloaded_res.scalars().all())

    return loaded_rules, created_count, updated_count, reused_count, type_breakdown


async def list_tender_rules(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    rule_type: Optional[ComplianceRuleType] = None,
    enabled: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[ComplianceRule], int, Dict[str, int]]:
    """List compiled compliance rules with filters and pagination."""
    await get_tender_by_id(session, tender_id, organization_id)

    query = (
        select(ComplianceRule)
        .options(
            selectinload(ComplianceRule.requirement).selectinload(TenderRequirement.clause),
        )
        .where(ComplianceRule.tender_id == tender_id)
    )

    if rule_type:
        query = query.where(ComplianceRule.rule_type == rule_type)
    if enabled is not None:
        query = query.where(ComplianceRule.enabled == enabled)

    # Get total count and type breakdown
    all_rules_stmt = select(ComplianceRule).where(ComplianceRule.tender_id == tender_id)
    all_res = await session.execute(all_rules_stmt)
    all_rules = list(all_res.scalars().all())

    type_breakdown: Dict[str, int] = {}
    for r in all_rules:
        type_breakdown[r.rule_type.value] = type_breakdown.get(r.rule_type.value, 0) + 1

    total = len(all_rules)
    if rule_type or enabled is not None:
        filtered_stmt = query
        filtered_res = await session.execute(filtered_stmt)
        total = len(list(filtered_res.scalars().all()))

    paginated_query = (
        query.order_by(ComplianceRule.sequence_order.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(paginated_query)
    items = list(result.scalars().all())

    return items, total, type_breakdown


async def get_compliance_rule_by_id(
    session: AsyncSession,
    tender_id: uuid.UUID,
    rule_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> ComplianceRule:
    """Retrieve a single rule with source requirement and clause metadata."""
    await get_tender_by_id(session, tender_id, organization_id)

    stmt = (
        select(ComplianceRule)
        .options(
            selectinload(ComplianceRule.requirement).selectinload(TenderRequirement.clause),
        )
        .where(
            ComplianceRule.id == rule_id,
            ComplianceRule.tender_id == tender_id,
        )
    )
    res = await session.execute(stmt)
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance rule {rule_id} not found for tender {tender_id}.",
        )
    return rule
