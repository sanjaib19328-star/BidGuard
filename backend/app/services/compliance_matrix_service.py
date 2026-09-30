import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bidder import Bidder, BidderDocument, ExtractedEntity
from app.models.clause import TenderClause
from app.models.compliance_matrix import EvaluationMatrixItem
from app.models.compliance_rule import ComplianceRule
from app.models.enums import (
    BidderDocumentType,
    ClauseCategory,
    ComplianceRuleType,
    EntityType,
    MatrixItemStatus,
    MseCategory,
    RequirementOperator,
    VerificationResultStatus,
)
from app.models.requirement import TenderRequirement
from app.models.tender import Tender
from app.models.verification import VerificationResult
from app.services.compliance_evaluation_service import normalize_numeric_value


def _build_tender_citation(clause: Optional[TenderClause], requirement: Optional[TenderRequirement]) -> Optional[Dict[str, Any]]:
    if not clause:
        return None
    return {
        "source_type": "TENDER",
        "document_id": str(clause.document_id) if clause.document_id else None,
        "clause_number": clause.clause_number,
        "page_number": clause.page_number,
        "title": clause.title,
        "snippet": requirement.requirement_text[:250] if requirement else clause.content[:250],
    }


def _build_bidder_citation(doc: Optional[BidderDocument], entity: Optional[ExtractedEntity]) -> Optional[Dict[str, Any]]:
    if not doc and not entity:
        return None
    return {
        "source_type": "BIDDER_DOCUMENT",
        "document_id": str(doc.id) if doc else (str(entity.document_id) if entity and entity.document_id else None),
        "document_type": doc.document_type.value if doc else None,
        "filename": doc.original_filename if doc else None,
        "page_number": entity.page_number if entity else (doc.total_pages if doc else 1),
        "snippet": entity.context_snippet if entity and entity.context_snippet else (f"Uploaded {doc.original_filename}" if doc else None),
    }


def _build_verification_citation(v_res: Optional[VerificationResult]) -> Optional[Dict[str, Any]]:
    if not v_res:
        return None
    return {
        "source_type": "GOVERNMENT",
        "verification_result_id": str(v_res.id),
        "data_source": v_res.source_type.value,
        "status": v_res.status.value,
        "verdict": v_res.name_match_verdict.value if v_res.name_match_verdict else None,
        "snippet": v_res.recommended_action or f"Verified via {v_res.source_type.value}",
    }


async def evaluate_tender_bidder_matrix(
    session: AsyncSession,
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> List[EvaluationMatrixItem]:
    """Execute complete multi-dimensional compliance matrix evaluation for a bidder against a tender."""
    # 1. Fetch Tender with compiled rules
    t_query = (
        select(Tender)
        .where(Tender.id == tender_id, Tender.organization_id == organization_id)
        .options(selectinload(Tender.documents))
    )
    t_res = await session.execute(t_query)
    tender = t_res.scalar_one_or_none()
    if not tender:
        raise ValueError("Tender not found or access denied.")

    # 2. Fetch ComplianceRules with Requirements & Clauses
    r_query = (
        select(ComplianceRule)
        .where(ComplianceRule.tender_id == tender_id)
        .options(
            selectinload(ComplianceRule.requirement).selectinload(TenderRequirement.clause)
        )
    )
    r_res = await session.execute(r_query)
    rules = list(r_res.scalars().all())

    # 3. Fetch Bidder Profile
    b_query = select(Bidder).where(Bidder.id == bidder_id, Bidder.organization_id == organization_id)
    b_res = await session.execute(b_query)
    bidder = b_res.scalar_one_or_none()
    if not bidder:
        raise ValueError("Bidder not found or access denied.")

    # 4. Fetch Bidder Documents & Extracted Entities
    doc_query = select(BidderDocument).where(BidderDocument.bidder_id == bidder_id)
    doc_res = await session.execute(doc_query)
    bidder_docs = list(doc_res.scalars().all())
    doc_type_map = {d.document_type: d for d in bidder_docs}

    ent_query = select(ExtractedEntity).where(ExtractedEntity.bidder_id == bidder_id)
    ent_res = await session.execute(ent_query)
    entities = list(ent_res.scalars().all())
    ent_type_map: Dict[EntityType, List[ExtractedEntity]] = {}
    for e in entities:
        ent_type_map.setdefault(e.entity_type, []).append(e)

    # 5. Fetch External Verification Results
    ver_query = select(VerificationResult).where(VerificationResult.bidder_id == bidder_id)
    ver_res = await session.execute(ver_query)
    verifications = list(ver_res.scalars().all())
    ver_map = {v.source_type.value: v for v in verifications}

    # 6. Check tender-level MSE policy
    # By default in CPCL / GeM tenders, MSE exemptions for turnover and experience apply unless explicitly denied
    tender_text_lower = " ".join([d.original_filename for d in tender.documents]).lower()
    tender_denies_mse_exemption = "mse exemption for years of experience and turnover: no" in tender_text_lower

    matrix_items: List[EvaluationMatrixItem] = []

    for rule in rules:
        req = rule.requirement
        clause = req.clause if req else None
        dimension = clause.category.value if clause and clause.category else "ELIGIBILITY"
        is_statutory = dimension in ("STATUTORY", "LEGAL") or (req and req.requirement_type.value == "STATUTORY")

        citations: List[Dict[str, Any]] = []
        t_cit = _build_tender_citation(clause, req)
        if t_cit:
            citations.append(t_cit)

        status_result = MatrixItemStatus.NOT_VERIFIABLE
        required_display = None
        bidder_display = None
        deviation_mag = None
        confidence = 1.0
        notes = None

        # A. Required Document Rules (e.g. GST, PAN, Udyam, ASME, Zero Deviation, Integrity Pact)
        if rule.rule_type == ComplianceRuleType.REQUIRED_DOCUMENT:
            doc_type_str = rule.target_document_type or (rule.rule_logic.get("document_type") if rule.rule_logic else None)
            required_display = f"Document: {doc_type_str}"

            # Match with bidder documents
            matched_doc = None
            if doc_type_str:
                for dt, d in doc_type_map.items():
                    if dt.value == doc_type_str or doc_type_str.lower() in dt.value.lower():
                        matched_doc = d
                        break

            if matched_doc:
                status_result = MatrixItemStatus.COMPLIANT
                bidder_display = f"Submitted {matched_doc.original_filename} ({matched_doc.document_type.value})"
                b_cit = _build_bidder_citation(matched_doc, None)
                if b_cit:
                    citations.append(b_cit)
                notes = f"Verified presence of mandatory document '{matched_doc.original_filename}'."
            else:
                status_result = MatrixItemStatus.NON_COMPLIANT
                bidder_display = "Document missing from submission"
                notes = f"Mandatory submission '{doc_type_str}' was not found in bidder uploaded documents."

        # B. Numeric Threshold & Range Rules (Turnover, Pressure, Thickness, Past Experience)
        elif rule.rule_type in (ComplianceRuleType.NUMERIC_THRESHOLD, ComplianceRuleType.NUMERIC_RANGE):
            target_metric = rule.target_metric or (rule.rule_logic.get("metric") if rule.rule_logic else "metric")
            req_op = rule.operator.value if rule.operator else ">="
            req_val = rule.threshold_value or 0.0
            req_unit = rule.unit or ""
            required_display = f"{target_metric} {req_op} {req_val} {req_unit}".strip()

            # Check MSE Exemption for Turnover or Past Experience
            is_turnover_or_exp = any(k in target_metric.lower() for k in ("turnover", "experience", "financial"))
            bidder_is_mse = bidder.is_mse or bidder.mse_category in (MseCategory.MICRO, MseCategory.SMALL)

            if is_turnover_or_exp and bidder_is_mse:
                if tender_denies_mse_exemption:
                    notes = "Tender explicitly excludes MSE relaxation for turnover/experience criteria."
                else:
                    # Verified MSE exemption
                    status_result = MatrixItemStatus.EXEMPT_MSE
                    bidder_display = f"MSE Registered ({bidder.mse_category.value}) - Relaxation Claimed"
                    udyam_ver = ver_map.get("UDYAM_MSME")
                    if udyam_ver:
                        citations.append(_build_verification_citation(udyam_ver))
                    notes = f"Bidder qualifies for Micro & Small Enterprise exemption per GeM PPP-MSE Policy."
                    # Continue to next rule as this is fully resolved as EXEMPT_MSE
                    item = EvaluationMatrixItem(
                        tender_id=tender_id,
                        bidder_id=bidder_id,
                        compliance_rule_id=rule.id,
                        requirement_id=req.id if req else None,
                        dimension=dimension,
                        status=status_result,
                        required_value=required_display,
                        bidder_extracted_value=bidder_display,
                        deviation_magnitude=0.0,
                        is_statutory=is_statutory,
                        confidence_score=confidence,
                        citations=citations,
                        notes=notes,
                    )
                    matrix_items.append(item)
                    continue

            # Find matching entity from bidder extraction
            matched_entity = None
            if "turnover" in target_metric.lower() and EntityType.FINANCIAL_TURNOVER in ent_type_map:
                matched_entity = ent_type_map[EntityType.FINANCIAL_TURNOVER][0]
            elif "pressure" in target_metric.lower() and EntityType.PRESSURE_VALUE in ent_type_map:
                matched_entity = ent_type_map[EntityType.PRESSURE_VALUE][0]
            elif "thickness" in target_metric.lower() and EntityType.THICKNESS_VALUE in ent_type_map:
                matched_entity = ent_type_map[EntityType.THICKNESS_VALUE][0]

            if matched_entity:
                bidder_display = f"{matched_entity.entity_value} (Extracted p.{matched_entity.page_number})"
                b_cit = _build_bidder_citation(None, matched_entity)
                if b_cit:
                    citations.append(b_cit)

                try:
                    num_match = re.search(r"[-+]?\d*\.\d+|\d+", matched_entity.entity_value.replace(",", ""))
                    actual_num = float(num_match.group(0)) if num_match else None
                    if actual_num is not None:
                        # Compare
                        if req_op in (">=", ">"):
                            passed = actual_num >= req_val
                            deviation_mag = round(actual_num - req_val, 2)
                        elif req_op in ("<=", "<"):
                            passed = actual_num <= req_val
                            deviation_mag = round(req_val - actual_num, 2)
                        elif req_op == "==":
                            passed = actual_num == req_val
                            deviation_mag = 0.0
                        else:
                            passed = actual_num >= req_val
                            deviation_mag = round(actual_num - req_val, 2)

                        if passed:
                            status_result = MatrixItemStatus.COMPLIANT
                            notes = f"Metric satisfies requirement ({actual_num} vs required {req_val})."
                        else:
                            status_result = MatrixItemStatus.NON_COMPLIANT
                            notes = f"Technical/financial shortfall detected: {actual_num} does not meet requirement {req_val}."
                    else:
                        status_result = MatrixItemStatus.NOT_VERIFIABLE
                        notes = "Could not parse numeric scalar from extracted entity value."
                except Exception as ex:
                    status_result = MatrixItemStatus.NOT_VERIFIABLE
                    notes = f"Evaluation error: {str(ex)}"
            else:
                status_result = MatrixItemStatus.NOT_VERIFIABLE
                bidder_display = "No corresponding technical/financial metric extracted from bidder submission"
                notes = f"Bidder documents did not contain extracted values for '{target_metric}'."

        # C. Boolean & Existence Checks (e.g. ASME Stamp, Statutory Registrations)
        elif rule.rule_type in (ComplianceRuleType.BOOLEAN_REQUIREMENT, ComplianceRuleType.EXISTENCE_CHECK):
            target_field = rule.target_metric or "attribute"
            required_display = f"Requirement: {target_field} == TRUE"

            if "asme" in target_field.lower():
                if bidder.asme_stamp_holder:
                    status_result = MatrixItemStatus.COMPLIANT
                    bidder_display = f"ASME Stamp Authorized (Cert: {bidder.asme_certificate_number or 'Confirmed'})"
                    if EntityType.ASME_STAMP in ent_type_map:
                        citations.append(_build_bidder_citation(None, ent_type_map[EntityType.ASME_STAMP][0]))
                    notes = "Bidder possesses active ASME Code Stamp authorization."
                else:
                    status_result = MatrixItemStatus.NON_COMPLIANT
                    bidder_display = "ASME Stamp Not Held"
                    notes = "Bidder does not hold mandatory ASME Section VIII Div 1/2 authorization."

            elif "gst" in target_field.lower():
                v_gst = ver_map.get("GSTN_PORTAL")
                if v_gst:
                    citations.append(_build_verification_citation(v_gst))
                    if v_gst.status == VerificationResultStatus.VERIFIED:
                        status_result = MatrixItemStatus.COMPLIANT
                        bidder_display = f"GSTIN {bidder.gstin} Verified Active"
                        notes = "GSTIN verified active with matching legal identity."
                    elif v_gst.status == VerificationResultStatus.MISMATCH:
                        status_result = MatrixItemStatus.NON_COMPLIANT
                        bidder_display = f"GSTIN Verified with Legal Name Mismatch"
                        notes = "Legal identity mismatch against GST portal records."
                    elif v_gst.status == VerificationResultStatus.AUTH_REQUIRED:
                        status_result = MatrixItemStatus.NOT_VERIFIABLE
                        bidder_display = "Government Verification Auth Required"
                        notes = "Authorized government API credentials required for live verification."
                    else:
                        status_result = MatrixItemStatus.NON_COMPLIANT
                        bidder_display = f"GSTIN Status: {v_gst.status.value}"
                        notes = f"GSTIN verification failed with status {v_gst.status.value}."
                elif bidder.gstin:
                    status_result = MatrixItemStatus.PARTIAL
                    bidder_display = f"Declared GSTIN: {bidder.gstin} (Unverified)"
                    notes = "GSTIN declared on profile but external registry verification not executed."
                else:
                    status_result = MatrixItemStatus.NON_COMPLIANT
                    bidder_display = "No GSTIN provided"
                    notes = "Mandatory GSTIN is missing."

            elif "pan" in target_field.lower():
                v_pan = ver_map.get("CBDT_PAN")
                if v_pan:
                    citations.append(_build_verification_citation(v_pan))
                    if v_pan.status == VerificationResultStatus.VERIFIED:
                        status_result = MatrixItemStatus.COMPLIANT
                        bidder_display = f"PAN {bidder.pan} Verified Active"
                    else:
                        status_result = MatrixItemStatus.NON_COMPLIANT
                        bidder_display = f"PAN Status: {v_pan.status.value}"
                elif bidder.pan:
                    status_result = MatrixItemStatus.PARTIAL
                    bidder_display = f"Declared PAN: {bidder.pan} (Unverified)"
                else:
                    status_result = MatrixItemStatus.NON_COMPLIANT
                    bidder_display = "No PAN provided"

            else:
                status_result = MatrixItemStatus.NOT_VERIFIABLE
                bidder_display = "Pending Officer Verification"
                notes = "Rule requires qualitative documentary inspection."

        # D. Fallback / Other Rule Types
        else:
            required_display = req.requirement_text[:100] if req else "Tender Clause"
            status_result = MatrixItemStatus.NOT_VERIFIABLE
            bidder_display = "Pending Officer Verification"
            notes = "Complex narrative clause requires manual officer assessment."

        # Create matrix item record
        item = EvaluationMatrixItem(
            tender_id=tender_id,
            bidder_id=bidder_id,
            compliance_rule_id=rule.id,
            requirement_id=req.id if req else None,
            dimension=dimension,
            status=status_result,
            required_value=required_display,
            bidder_extracted_value=bidder_display,
            deviation_magnitude=deviation_mag,
            is_statutory=is_statutory,
            confidence_score=confidence,
            citations=citations,
            notes=notes,
        )
        matrix_items.append(item)

    # Persist in DB (replace older matrix items for this bidder/tender if any)
    existing_q = select(EvaluationMatrixItem).where(
        EvaluationMatrixItem.tender_id == tender_id,
        EvaluationMatrixItem.bidder_id == bidder_id,
    )
    existing_res = await session.execute(existing_q)
    for old_item in existing_res.scalars().all():
        await session.delete(old_item)

    for item in matrix_items:
        session.add(item)

    await session.commit()
    for item in matrix_items:
        await session.refresh(item)

    return matrix_items
