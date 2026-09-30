from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import (
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
    NameMatchVerdict,
    VerificationResultStatus,
)
from app.models.verification import VerificationResult


def calculate_deterministic_risk_score(
    critical_count: int,
    high_count: int,
    medium_count: int,
    low_count: int,
    unverifiable_count: int = 0,
) -> Tuple[float, FindingSeverity]:
    """Calculate an analytical risk indicator from 0.0 to 100.0% and assign a risk level.
    
    CRITICAL: 35% each
    HIGH: 20% each
    MEDIUM: 10% each
    LOW: 3% each
    UNVERIFIABLE: 5% each
    """
    raw_score = (
        critical_count * 35.0
        + high_count * 20.0
        + medium_count * 10.0
        + low_count * 3.0
        + unverifiable_count * 5.0
    )
    score = min(round(raw_score, 1), 100.0)

    if critical_count > 0 or score >= 70.0:
        level = FindingSeverity.CRITICAL
    elif high_count > 0 or score >= 40.0:
        level = FindingSeverity.HIGH
    elif score >= 15.0 or medium_count >= 2:
        level = FindingSeverity.MEDIUM
    else:
        level = FindingSeverity.LOW

    return score, level


async def generate_officer_findings(
    session: AsyncSession,
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
) -> Tuple[List[OfficerFinding], Dict[str, Any]]:
    """Analyze compliance matrix items and verification results to synthesize officer findings."""
    # 1. Fetch EvaluationMatrixItems for this tender + bidder
    m_query = (
        select(EvaluationMatrixItem)
        .where(
            EvaluationMatrixItem.tender_id == tender_id,
            EvaluationMatrixItem.bidder_id == bidder_id,
        )
        .options(selectinload(EvaluationMatrixItem.compliance_rule))
    )
    m_res = await session.execute(m_query)
    matrix_items = list(m_res.scalars().all())

    # 2. Fetch Verification Results
    v_query = select(VerificationResult).where(VerificationResult.bidder_id == bidder_id)
    v_res = await session.execute(v_query)
    verifications = list(v_res.scalars().all())

    findings: List[OfficerFinding] = []

    # 3. Analyze External Verification Results for Findings
    for v in verifications:
        if v.status == VerificationResultStatus.MISMATCH:
            is_serious = v.name_match_verdict == NameMatchVerdict.SERIOUS_MISMATCH
            severity = FindingSeverity.CRITICAL if is_serious else FindingSeverity.HIGH
            title = f"Statutory Identity Mismatch ({v.source_type.value})"
            desc = (
                f"External registry verification for {v.source_type.value} detected identity discrepancy. "
                f"Verdict: {v.name_match_verdict.value if v.name_match_verdict else 'MISMATCH'}. "
                f"Discrepancies: {v.discrepancies}"
            )
            f = OfficerFinding(
                tender_id=tender_id,
                bidder_id=bidder_id,
                matrix_item_id=None,
                severity=severity,
                finding_type=FindingType.IDENTITY_MISMATCH,
                title=title,
                description=desc,
                evidence_data={
                    "source": v.source_type.value,
                    "matched_fields": v.matched_fields,
                    "discrepancies": v.discrepancies,
                },
                recommended_action=v.recommended_action or "Issue formal notice requiring bidder to clarify legal identity discrepancy.",
                review_status=FindingReviewStatus.PENDING,
            )
            findings.append(f)

        elif v.status == VerificationResultStatus.INVALID_FORMAT:
            f = OfficerFinding(
                tender_id=tender_id,
                bidder_id=bidder_id,
                matrix_item_id=None,
                severity=FindingSeverity.HIGH,
                finding_type=FindingType.IDENTITY_MISMATCH,
                title=f"Invalid Statutory Identifier ({v.source_type.value})",
                description=f"Identifier provided by bidder failed official format rules: {v.discrepancies}",
                evidence_data={"source": v.source_type.value, "discrepancies": v.discrepancies},
                recommended_action="Request bidder to submit valid official registration certificate with proper identifier structure.",
                review_status=FindingReviewStatus.PENDING,
            )
            findings.append(f)

        elif v.status == VerificationResultStatus.AUTH_REQUIRED:
            f = OfficerFinding(
                tender_id=tender_id,
                bidder_id=bidder_id,
                matrix_item_id=None,
                severity=FindingSeverity.MEDIUM,
                finding_type=FindingType.IDENTITY_MISMATCH,
                title=f"Government API Authorization Required ({v.source_type.value})",
                description="Live external government verification could not execute because official API credentials are not configured. Anti-hallucination guard enforced.",
                evidence_data={"source": v.source_type.value, "message": "Authorized connection required. External government verification not executed."},
                recommended_action="Procurement officer should configure live credentials in Data Source settings or verify manual physical documents.",
                review_status=FindingReviewStatus.PENDING,
            )
            findings.append(f)

    # 4. Analyze EvaluationMatrixItems for Findings
    for item in matrix_items:
        rule = item.compliance_rule
        req_val = item.required_value or "Requirement"
        bidder_val = item.bidder_extracted_value or "None"

        if item.status == MatrixItemStatus.NON_COMPLIANT:
            # Determine severity and type
            if "zero deviation" in req_val.lower() or "integrity pact" in req_val.lower():
                severity = FindingSeverity.CRITICAL
                finding_type = FindingType.MISSING_DOCUMENT
                title = f"Mandatory Undertaking Missing ({req_val})"
                rec_action = "Mandatory zero-deviation/integrity declaration is absent; disqualification risk per tender clause."
            elif "asme" in req_val.lower():
                severity = FindingSeverity.CRITICAL
                finding_type = FindingType.TECHNICAL_SHORTFALL
                title = "ASME Code Stamp Authorization Missing"
                rec_action = "Seek confirmation of active ASME Section VIII Div 1/2 authorization certificate."
            elif "pressure" in req_val.lower() or "thickness" in req_val.lower():
                severity = FindingSeverity.CRITICAL
                finding_type = FindingType.TECHNICAL_SHORTFALL
                title = f"Technical Parameter Non-Compliance ({req_val})"
                rec_action = f"Technical shortfall of {item.deviation_magnitude or 0.0} detected against tender design requirements."
            elif "turnover" in req_val.lower() or "financial" in req_val.lower():
                severity = FindingSeverity.HIGH
                finding_type = FindingType.VALUE_SHORTFALL
                title = f"Financial Turnover Shortfall ({req_val})"
                rec_action = "Verify if bidder holds MSE exemption, or request audited balance sheets / CA certificate."
            elif "document" in req_val.lower():
                severity = FindingSeverity.HIGH
                finding_type = FindingType.MISSING_DOCUMENT
                title = f"Mandatory Document Missing: {req_val}"
                rec_action = "Issue clarification letter to bidder to submit missing document within allowed window."
            else:
                severity = FindingSeverity.HIGH
                finding_type = FindingType.COMMERCIAL_DEVIATION
                title = f"Non-Compliance with Requirement: {req_val[:60]}"
                rec_action = "Review requirement and bidder documentation for potential deviation."

            f = OfficerFinding(
                tender_id=tender_id,
                bidder_id=bidder_id,
                matrix_item_id=item.id,
                severity=severity,
                finding_type=finding_type,
                title=title,
                description=f"Requirement: {req_val}. Bidder submission: {bidder_val}. Notes: {item.notes or ''}",
                evidence_data={"citations": item.citations, "notes": item.notes},
                recommended_action=rec_action,
                review_status=FindingReviewStatus.PENDING,
            )
            findings.append(f)

        elif item.status == MatrixItemStatus.PARTIAL:
            f = OfficerFinding(
                tender_id=tender_id,
                bidder_id=bidder_id,
                matrix_item_id=item.id,
                severity=FindingSeverity.MEDIUM,
                finding_type=FindingType.VALUE_SHORTFALL,
                title=f"Partial Information Demonstrated: {req_val[:60]}",
                description=f"Bidder submitted partial evidence ({bidder_val}). Full requirement validation cannot be confirmed.",
                evidence_data={"citations": item.citations},
                recommended_action="Officer documentary review required to evaluate complete compliance.",
                review_status=FindingReviewStatus.PENDING,
            )
            findings.append(f)

    # 5. Persist Findings (delete existing pending findings to re-evaluate freshly)
    existing_f_q = select(OfficerFinding).where(
        OfficerFinding.tender_id == tender_id,
        OfficerFinding.bidder_id == bidder_id,
        OfficerFinding.review_status == FindingReviewStatus.PENDING,
    )
    existing_f_res = await session.execute(existing_f_q)
    for old_f in existing_f_res.scalars().all():
        await session.delete(old_f)

    for f in findings:
        session.add(f)

    await session.commit()
    for f in findings:
        await session.refresh(f)

    # 6. Compute Analytical Risk Summary
    crit = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
    high = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
    med = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
    low = sum(1 for f in findings if f.severity == FindingSeverity.LOW)
    unverifiable = sum(1 for item in matrix_items if item.status == MatrixItemStatus.NOT_VERIFIABLE)

    risk_score, risk_level = calculate_deterministic_risk_score(crit, high, med, low, unverifiable)

    summary = {
        "tender_id": str(tender_id),
        "bidder_id": str(bidder_id),
        "total_matrix_items": len(matrix_items),
        "total_findings": len(findings),
        "critical_findings": crit,
        "high_findings": high,
        "medium_findings": med,
        "low_findings": low,
        "unverifiable_items": unverifiable,
        "risk_indicator_score": risk_score,
        "risk_level": risk_level.value,
        "disclaimer": (
            "The risk indicator score and findings represent analytical risk indicators to assist "
            "the procurement officer. BidGuard AI does NOT produce autonomous qualification or disqualification decisions."
        ),
    }

    return findings, summary


async def review_officer_finding(
    session: AsyncSession,
    finding_id: uuid.UUID,
    new_status: FindingReviewStatus,
    officer_notes: Optional[str],
    user_id: uuid.UUID,
) -> OfficerFinding:
    """Execute officer decision (ACCEPT, REJECT, OVERRIDE, CLARIFICATION_REQUESTED) with strict justification guardrails."""
    q = select(OfficerFinding).where(OfficerFinding.id == finding_id)
    res = await session.execute(q)
    finding = res.scalar_one_or_none()
    if not finding:
        raise ValueError("Officer finding not found.")

    # Strict Override Guardrail: Officer Notes MUST be provided
    if new_status == FindingReviewStatus.OVERRIDDEN:
        if not officer_notes or not officer_notes.strip():
            raise ValueError("Officer justification notes are strictly mandatory when overriding a compliance finding.")

    finding.review_status = new_status
    if officer_notes:
        finding.officer_notes = officer_notes.strip()

    if new_status == FindingReviewStatus.OVERRIDDEN:
        from datetime import datetime, timezone
        finding.overridden_by_user_id = user_id
        finding.overridden_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(finding)
    return finding
