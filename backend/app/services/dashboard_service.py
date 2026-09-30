from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.bidder import Bidder
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import (
    DataSourceType,
    FindingReviewStatus,
    FindingSeverity,
    MatrixItemStatus,
    TenderStatus,
    VerificationResultStatus,
)
from app.models.tender import Tender
from app.models.verification import VerificationRequest, VerificationResult


async def get_procurement_dashboard_metrics(
    session: AsyncSession,
    organization_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Compute comprehensive executive procurement analytics and KPI metrics for an organization.
    All aggregations strictly enforce multi-tenant isolation via organization_id.
    """
    # 1. Tender Metrics
    tender_query = (
        select(Tender.status, func.count(Tender.id))
        .where(Tender.organization_id == organization_id)
        .group_by(Tender.status)
    )
    tender_res = await session.execute(tender_query)
    tender_counts = dict(tender_res.all())

    total_tenders = sum(tender_counts.values())
    active_statuses = [
        TenderStatus.DRAFT,
        TenderStatus.PROCESSING,
        TenderStatus.READY,
        TenderStatus.UNDER_REVIEW,
    ]
    active_tenders = sum(tender_counts.get(st, 0) for st in active_statuses)
    under_review_tenders = tender_counts.get(TenderStatus.UNDER_REVIEW, 0)
    completed_tenders = tender_counts.get(TenderStatus.COMPLETED, 0)
    archived_tenders = tender_counts.get(TenderStatus.ARCHIVED, 0)

    # 2. Bidder Metrics
    bidder_count_q = (
        select(
            func.count(Bidder.id).label("total"),
            func.count(Bidder.id).filter(Bidder.is_mse.is_(True)).label("mse_count"),
        )
        .where(Bidder.organization_id == organization_id)
    )
    bidder_count_res = await session.execute(bidder_count_q)
    b_row = bidder_count_res.one_or_none()
    total_bidders = b_row.total if b_row else 0
    mse_bidders_count = b_row.mse_count if b_row else 0

    # Evaluated bidders (distinct bidders with at least one EvaluationMatrixItem in this org)
    eval_bidders_q = (
        select(func.count(distinct(EvaluationMatrixItem.bidder_id)))
        .join(Tender, EvaluationMatrixItem.tender_id == Tender.id)
        .where(Tender.organization_id == organization_id)
    )
    eval_bidders_res = await session.execute(eval_bidders_q)
    evaluated_bidders = eval_bidders_res.scalar_one() or 0
    pending_bidders = max(0, total_bidders - evaluated_bidders)

    # 3. Compliance Matrix Metrics
    matrix_query = (
        select(EvaluationMatrixItem.status, func.count(EvaluationMatrixItem.id))
        .join(Tender, EvaluationMatrixItem.tender_id == Tender.id)
        .where(Tender.organization_id == organization_id)
        .group_by(EvaluationMatrixItem.status)
    )
    matrix_res = await session.execute(matrix_query)
    matrix_counts = {
        (k.value if hasattr(k, "value") else str(k)): v
        for k, v in matrix_res.all()
    }

    total_matrix_items = sum(matrix_counts.values())
    compliant_count = matrix_counts.get(MatrixItemStatus.COMPLIANT.value, 0)
    exempt_mse_count = matrix_counts.get(MatrixItemStatus.EXEMPT_MSE.value, 0)
    non_compliant_count = matrix_counts.get(MatrixItemStatus.NON_COMPLIANT.value, 0)
    partial_count = matrix_counts.get(MatrixItemStatus.PARTIAL.value, 0)
    not_verifiable_count = matrix_counts.get(MatrixItemStatus.NOT_VERIFIABLE.value, 0)

    evaluated_matrix_items = compliant_count + exempt_mse_count + non_compliant_count + partial_count
    overall_compliance_rate_percent = (
        round(((compliant_count + exempt_mse_count) / evaluated_matrix_items) * 100.0, 1)
        if evaluated_matrix_items > 0
        else 0.0
    )

    # 4. Officer Findings & Risk Metrics
    findings_sev_q = (
        select(OfficerFinding.severity, func.count(OfficerFinding.id))
        .join(Tender, OfficerFinding.tender_id == Tender.id)
        .where(Tender.organization_id == organization_id)
        .group_by(OfficerFinding.severity)
    )
    findings_sev_res = await session.execute(findings_sev_q)
    sev_counts = {
        (k.value if hasattr(k, "value") else str(k)): v
        for k, v in findings_sev_res.all()
    }

    findings_rev_q = (
        select(OfficerFinding.review_status, func.count(OfficerFinding.id))
        .join(Tender, OfficerFinding.tender_id == Tender.id)
        .where(Tender.organization_id == organization_id)
        .group_by(OfficerFinding.review_status)
    )
    findings_rev_res = await session.execute(findings_rev_q)
    rev_counts = {
        (k.value if hasattr(k, "value") else str(k)): v
        for k, v in findings_rev_res.all()
    }

    total_findings = sum(sev_counts.values())
    unresolved_q = (
        select(func.count(OfficerFinding.id))
        .join(Tender, OfficerFinding.tender_id == Tender.id)
        .where(
            Tender.organization_id == organization_id,
            OfficerFinding.severity.in_([FindingSeverity.CRITICAL, FindingSeverity.HIGH]),
            OfficerFinding.review_status.in_([
                FindingReviewStatus.PENDING,
                FindingReviewStatus.CLARIFICATION_REQUESTED,
            ]),
        )
    )
    unresolved_res = await session.execute(unresolved_q)
    unresolved_critical_high = unresolved_res.scalar_one() or 0

    # 5. Verification Metrics
    verif_type_q = (
        select(VerificationRequest.verification_type, func.count(VerificationRequest.id))
        .where(VerificationRequest.organization_id == organization_id)
        .group_by(VerificationRequest.verification_type)
    )
    verif_type_res = await session.execute(verif_type_q)
    verif_type_counts = {
        (k.value if hasattr(k, "value") else str(k)): v
        for k, v in verif_type_res.all()
    }

    verif_res_q = (
        select(VerificationResult.status, func.count(VerificationResult.id))
        .join(VerificationRequest, VerificationResult.verification_request_id == VerificationRequest.id)
        .where(VerificationRequest.organization_id == organization_id)
        .group_by(VerificationResult.status)
    )
    verif_res_res = await session.execute(verif_res_q)
    verif_status_counts = {
        (k.value if hasattr(k, "value") else str(k)): v
        for k, v in verif_res_res.all()
    }


    # 6. Recent Activity (latest 10 audit logs)
    audit_q = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    audit_res = await session.execute(audit_q)
    recent_logs = audit_res.scalars().all()
    recent_activity = [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "actor_user_id": str(log.actor_user_id) if log.actor_user_id else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in recent_logs
    ]

    return {
        "generated_at": datetime.now().isoformat(),
        "disclaimer": (
            "BidGuard AI is a non-autonomous procurement decision support system. "
            "All metrics and evaluations are advisory and subject to statutory authority review."
        ),
        "tender_metrics": {
            "total_tenders": total_tenders,
            "active_tenders": active_tenders,
            "under_review_tenders": under_review_tenders,
            "completed_tenders": completed_tenders,
            "archived_tenders": archived_tenders,
        },
        "bidder_metrics": {
            "total_bidders": total_bidders,
            "evaluated_bidders": evaluated_bidders,
            "pending_bidders": pending_bidders,
            "mse_bidders_count": mse_bidders_count,
        },
        "compliance_matrix_metrics": {
            "total_matrix_items": total_matrix_items,
            "compliant_count": compliant_count,
            "exempt_mse_count": exempt_mse_count,
            "non_compliant_count": non_compliant_count,
            "partial_count": partial_count,
            "not_verifiable_count": not_verifiable_count,
            "overall_compliance_rate_percent": overall_compliance_rate_percent,
        },
        "risk_findings_metrics": {
            "total_findings": total_findings,
            "unresolved_critical_high": unresolved_critical_high,
            "by_severity": {
                "CRITICAL": sev_counts.get(FindingSeverity.CRITICAL.value, 0),
                "HIGH": sev_counts.get(FindingSeverity.HIGH.value, 0),
                "MEDIUM": sev_counts.get(FindingSeverity.MEDIUM.value, 0),
                "LOW": sev_counts.get(FindingSeverity.LOW.value, 0),
            },
            "by_review_status": {
                "PENDING": rev_counts.get(FindingReviewStatus.PENDING.value, 0),
                "ACCEPTED": rev_counts.get(FindingReviewStatus.ACCEPTED.value, 0),
                "REJECTED": rev_counts.get(FindingReviewStatus.REJECTED.value, 0),
                "OVERRIDDEN": rev_counts.get(FindingReviewStatus.OVERRIDDEN.value, 0),
                "CLARIFICATION_REQUESTED": rev_counts.get(
                    FindingReviewStatus.CLARIFICATION_REQUESTED.value, 0
                ),
            },
        },
        "verification_metrics": {
            "total_requests": sum(verif_type_counts.values()),
            "by_type": verif_type_counts,
            "by_status": verif_status_counts,
        },
        "recent_activity": recent_activity,
    }
