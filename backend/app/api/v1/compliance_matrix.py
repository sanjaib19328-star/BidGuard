from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.models.tender import Tender
from app.models.compliance_matrix import EvaluationMatrixItem, OfficerFinding
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.compliance_matrix import (
    BidderComparisonResponse,
    EvaluationMatrixItemResponse,
    EvaluationMatrixResponse,
    OfficerFindingListResponse,
    OfficerFindingResponse,
    OfficerFindingReviewRequest,
)
from app.services import (
    bidder_comparison_service,
    compliance_matrix_service,
    risk_intelligence_service,
)
from app.services.audit_service import log_audit_event

router = APIRouter(tags=["Compliance Matrix & Risk Intelligence"])


@router.post(
    "/tenders/{tender_id}/bidders/{bidder_id}/evaluate-matrix",
    response_model=EvaluationMatrixResponse,
    summary="Generate compliance evaluation matrix",
    description="Evaluate tender compliance rules against bidder documents, extracted entities, and government verifications.",
)
async def evaluate_matrix(
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    try:
        items = await compliance_matrix_service.evaluate_tender_bidder_matrix(
            session=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            organization_id=current_user.organization_id,
        )
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))

    # Auto-generate findings & risk score
    await risk_intelligence_service.generate_officer_findings(
        session=db,
        tender_id=tender_id,
        bidder_id=bidder_id,
    )

    await log_audit_event(
        session=db,
        action="COMPLIANCE_MATRIX_EVALUATED",
        entity_type="evaluation_matrix",
        entity_id=f"{tender_id}:{bidder_id}",
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        new_state={"total_rules_evaluated": len(items)},
    )
    await db.commit()

    item_responses = [EvaluationMatrixItemResponse.model_validate(it) for it in items]
    return EvaluationMatrixResponse(
        tender_id=tender_id,
        bidder_id=bidder_id,
        items=item_responses,
        total=len(item_responses),
    )


@router.get(
    "/tenders/{tender_id}/bidders/{bidder_id}/matrix",
    response_model=EvaluationMatrixResponse,
    summary="Get bidder evaluation matrix items",
    description="Retrieve all evaluated compliance matrix items for a bidder against a tender.",
)
async def get_matrix(
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR])),
):
    # Verify Tender exists and belongs to current user's organization
    t_query = select(Tender).where(Tender.id == tender_id, Tender.organization_id == current_user.organization_id)
    t_res = await db.execute(t_query)
    if not t_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found or access denied.")

    q = (
        select(EvaluationMatrixItem)
        .where(
            EvaluationMatrixItem.tender_id == tender_id,
            EvaluationMatrixItem.bidder_id == bidder_id,
        )
        .order_by(EvaluationMatrixItem.dimension, EvaluationMatrixItem.created_at)
    )
    res = await db.execute(q)
    items = list(res.scalars().all())

    item_responses = [EvaluationMatrixItemResponse.model_validate(it) for it in items]
    return EvaluationMatrixResponse(
        tender_id=tender_id,
        bidder_id=bidder_id,
        items=item_responses,
        total=len(item_responses),
    )


@router.get(
    "/tenders/{tender_id}/bidders/{bidder_id}/findings",
    response_model=OfficerFindingListResponse,
    summary="Get officer risk findings",
    description="Retrieve all prioritized risk findings and discrepancies synthesized for officer review.",
)
async def get_findings(
    tender_id: uuid.UUID,
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR])),
):
    # Verify Tender exists and belongs to current user's organization
    t_query = select(Tender).where(Tender.id == tender_id, Tender.organization_id == current_user.organization_id)
    t_res = await db.execute(t_query)
    if not t_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found or access denied.")

    findings, summary = await risk_intelligence_service.generate_officer_findings(
        session=db,
        tender_id=tender_id,
        bidder_id=bidder_id,
    )
    finding_responses = [OfficerFindingResponse.model_validate(f) for f in findings]
    return OfficerFindingListResponse(items=finding_responses, summary=summary)


@router.patch(
    "/compliance/findings/{finding_id}/review",
    response_model=OfficerFindingResponse,
    summary="Review officer finding",
    description="Record procurement officer decision (ACCEPT, REJECT, OVERRIDE, CLARIFICATION_REQUESTED). Override requires justification.",
)
async def review_finding(
    finding_id: uuid.UUID,
    data: OfficerFindingReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    # Verify finding exists and belongs to user's organization
    f_q = select(OfficerFinding).where(OfficerFinding.id == finding_id)
    f_res = await db.execute(f_q)
    finding = f_res.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer finding not found.")

    t_query = select(Tender).where(Tender.id == finding.tender_id, Tender.organization_id == current_user.organization_id)
    t_res = await db.execute(t_query)
    if not t_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found or access denied.")

    try:
        updated = await risk_intelligence_service.review_officer_finding(
            session=db,
            finding_id=finding_id,
            new_status=data.review_status,
            officer_notes=data.officer_notes,
            user_id=current_user.id,
        )
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))

    await log_audit_event(
        session=db,
        action="OFFICER_FINDING_REVIEWED",
        entity_type="officer_finding",
        entity_id=str(finding_id),
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        new_state={
            "review_status": updated.review_status.value,
            "officer_notes": updated.officer_notes,
        },
    )
    await db.commit()

    return OfficerFindingResponse.model_validate(updated)


@router.get(
    "/tenders/{tender_id}/compare-bidders",
    response_model=BidderComparisonResponse,
    summary="Compare bidders for a tender",
    description="Generate side-by-side compliance, risk, and statutory evidence comparison table.",
)
async def compare_bidders(
    tender_id: uuid.UUID,
    bidder_ids: Optional[List[uuid.UUID]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.AUDITOR])),
):
    try:
        comparison = await bidder_comparison_service.compare_bidders_for_tender(
            session=db,
            tender_id=tender_id,
            organization_id=current_user.organization_id,
            bidder_ids=bidder_ids,
        )
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))

    return BidderComparisonResponse(**comparison)
