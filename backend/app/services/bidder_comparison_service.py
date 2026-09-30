from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bidder import Bidder
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import FindingSeverity, MatrixItemStatus
from app.models.tender import Tender
from app.models.verification import VerificationResult
from app.services.risk_intelligence_service import calculate_deterministic_risk_score


async def compare_bidders_for_tender(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    bidder_ids: Optional[List[uuid.UUID]] = None,
) -> Dict[str, Any]:
    """Build multi-bidder side-by-side compliance and risk comparison table for a tender."""
    # 1. Verify Tender
    t_query = select(Tender).where(Tender.id == tender_id, Tender.organization_id == organization_id)
    t_res = await session.execute(t_query)
    tender = t_res.scalar_one_or_none()
    if not tender:
        raise ValueError("Tender not found or access denied.")

    # 2. Resolve Bidders
    b_query = select(Bidder).where(Bidder.organization_id == organization_id)
    if bidder_ids:
        b_query = b_query.where(Bidder.id.in_(bidder_ids))
    b_res = await session.execute(b_query)
    bidders = list(b_res.scalars().all())

    comparison_items: List[Dict[str, Any]] = []

    for b in bidders:
        # Fetch matrix items for this bidder on this tender
        m_query = select(EvaluationMatrixItem).where(
            EvaluationMatrixItem.tender_id == tender_id,
            EvaluationMatrixItem.bidder_id == b.id,
        )
        m_res = await session.execute(m_query)
        m_items = list(m_res.scalars().all())

        # Count matrix statuses
        compliant = sum(1 for m in m_items if m.status == MatrixItemStatus.COMPLIANT)
        non_compliant = sum(1 for m in m_items if m.status == MatrixItemStatus.NON_COMPLIANT)
        partial = sum(1 for m in m_items if m.status == MatrixItemStatus.PARTIAL)
        unverifiable = sum(1 for m in m_items if m.status == MatrixItemStatus.NOT_VERIFIABLE)
        exempt_mse = sum(1 for m in m_items if m.status == MatrixItemStatus.EXEMPT_MSE)

        # Fetch officer findings
        f_query = select(OfficerFinding).where(
            OfficerFinding.tender_id == tender_id,
            OfficerFinding.bidder_id == b.id,
        )
        f_res = await session.execute(f_query)
        findings = list(f_res.scalars().all())

        crit = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        med = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)
        low = sum(1 for f in findings if f.severity == FindingSeverity.LOW)

        risk_score, risk_level = calculate_deterministic_risk_score(crit, high, med, low, unverifiable)

        # Statutory verification summary
        v_query = select(VerificationResult).where(VerificationResult.bidder_id == b.id)
        v_res = await session.execute(v_query)
        verifications = list(v_res.scalars().all())
        statutory_summary = {v.source_type.value: v.status.value for v in verifications}

        bidder_row = {
            "bidder_id": str(b.id),
            "legal_name": b.legal_name,
            "trade_name": b.trade_name,
            "gstin": b.gstin,
            "pan": b.pan,
            "is_mse": b.is_mse,
            "mse_category": b.mse_category.value if b.mse_category else "NOT_APPLICABLE",
            "asme_stamp_holder": b.asme_stamp_holder,
            "asme_certificate_number": b.asme_certificate_number,
            "compliance_summary": {
                "total_rules_evaluated": len(m_items),
                "compliant": compliant,
                "non_compliant": non_compliant,
                "partial": partial,
                "not_verifiable": unverifiable,
                "exempt_mse": exempt_mse,
            },
            "findings_summary": {
                "total_findings": len(findings),
                "critical": crit,
                "high": high,
                "medium": med,
                "low": low,
            },
            "statutory_verifications": statutory_summary,
            "risk_indicator": {
                "score": risk_score,
                "level": risk_level.value,
            },
        }
        comparison_items.append(bidder_row)

    return {
        "tender_id": str(tender.id),
        "tender_title": tender.title,
        "tender_number": tender.tender_number,
        "total_bidders_compared": len(comparison_items),
        "comparison_table": comparison_items,
        "guardrail_notice": (
            "This comparison table provides objective multi-dimensional evidence and risk indicators. "
            "In strict adherence to procurement policy, BidGuard AI does not declare winners or rank bidders."
        ),
    }
