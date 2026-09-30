import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TenderStatus
from app.models.tender import Tender
from app.schemas.tender import (
    TenderCreateRequest,
    TenderUpdateRequest,
)
from app.services.audit_service import log_audit_event

ALLOWED_TRANSITIONS: Dict[TenderStatus, List[TenderStatus]] = {
    TenderStatus.DRAFT: [TenderStatus.PROCESSING, TenderStatus.READY, TenderStatus.ARCHIVED],
    TenderStatus.PROCESSING: [TenderStatus.READY, TenderStatus.DRAFT, TenderStatus.ARCHIVED],
    TenderStatus.READY: [TenderStatus.UNDER_REVIEW, TenderStatus.DRAFT, TenderStatus.ARCHIVED],
    TenderStatus.UNDER_REVIEW: [TenderStatus.COMPLETED, TenderStatus.READY, TenderStatus.ARCHIVED],
    TenderStatus.COMPLETED: [TenderStatus.ARCHIVED],
    TenderStatus.ARCHIVED: [],
}


def _tender_to_dict(tender: Tender) -> Dict[str, Any]:
    """Serialize tender entity to a dictionary for audit logs."""
    return {
        "id": str(tender.id),
        "organization_id": str(tender.organization_id),
        "tender_number": tender.tender_number,
        "title": tender.title,
        "description": tender.description,
        "procuring_entity": tender.procuring_entity,
        "department": tender.department,
        "category": tender.category,
        "tender_type": tender.tender_type,
        "source_portal": tender.source_portal,
        "source_url": tender.source_url,
        "issue_date": tender.issue_date.isoformat() if tender.issue_date else None,
        "submission_deadline": tender.submission_deadline.isoformat() if tender.submission_deadline else None,
        "opening_date": tender.opening_date.isoformat() if tender.opening_date else None,
        "status": tender.status.value,
        "created_by": str(tender.created_by) if tender.created_by else None,
    }


async def create_tender(
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    req: TenderCreateRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tender:
    """Create a new tender scoped to the authenticated user's organization."""
    # 1. Check duplicate tender number within organization
    query = select(Tender).where(
        Tender.organization_id == organization_id,
        func.lower(Tender.tender_number) == func.lower(req.tender_number),
    )
    res = await session.execute(query)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tender with number '{req.tender_number}' already exists in your organization.",
        )

    # 2. Instantiate tender
    tender = Tender(
        organization_id=organization_id,
        tender_number=req.tender_number.strip(),
        title=req.title.strip(),
        description=req.description,
        procuring_entity=req.procuring_entity,
        department=req.department,
        category=req.category,
        tender_type=req.tender_type,
        source_portal=req.source_portal or "GeM",
        source_url=str(req.source_url) if req.source_url else None,
        issue_date=req.issue_date,
        submission_deadline=req.submission_deadline,
        opening_date=req.opening_date,
        status=TenderStatus.DRAFT,
        created_by=user_id,
    )
    session.add(tender)
    await session.flush()
    await session.refresh(tender)

    # 3. Create Audit Record
    await log_audit_event(
        session=session,
        action="TENDER_CREATED",
        entity_type="tender",
        entity_id=str(tender.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state=_tender_to_dict(tender),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()
    await session.refresh(tender)
    return tender


async def list_tenders(
    session: AsyncSession,
    organization_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[TenderStatus] = None,
    search: Optional[str] = None,
) -> Tuple[List[Tender], int]:
    """List and filter tenders strictly scoped to the organization."""
    query = select(Tender).where(Tender.organization_id == organization_id)

    if status_filter:
        query = query.where(Tender.status == status_filter)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Tender.tender_number.ilike(term),
                Tender.title.ilike(term),
                Tender.procuring_entity.ilike(term),
                Tender.department.ilike(term),
            )
        )

    # Count total matching
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await session.execute(count_query)
    total = total_res.scalar_one()

    # Pagination & ordering
    offset = (page - 1) * page_size
    query = query.order_by(Tender.created_at.desc()).offset(offset).limit(page_size)

    items_res = await session.execute(query)
    items = list(items_res.scalars().all())

    return items, total


async def get_tender_by_id(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Tender:
    """Retrieve tender by ID with strict organization scoping."""
    query = select(Tender).where(
        Tender.id == tender_id,
        Tender.organization_id == organization_id,
    )
    res = await session.execute(query)
    tender = res.scalar_one_or_none()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )
    return tender


async def update_tender(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    req: TenderUpdateRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tender:
    """Update tender metadata fields."""
    tender = await get_tender_by_id(session, tender_id, organization_id)
    prev_state = _tender_to_dict(tender)

    # If tender_number is changing, ensure uniqueness in organization
    if req.tender_number and req.tender_number.strip().lower() != tender.tender_number.lower():
        dup_query = select(Tender).where(
            Tender.organization_id == organization_id,
            Tender.id != tender.id,
            func.lower(Tender.tender_number) == func.lower(req.tender_number.strip()),
        )
        dup_res = await session.execute(dup_query)
        if dup_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tender with number '{req.tender_number}' already exists in your organization.",
            )

    update_data = req.model_dump(exclude_unset=True)
    if "source_url" in update_data and update_data["source_url"] is not None:
        update_data["source_url"] = str(update_data["source_url"])

    for field, value in update_data.items():
        setattr(tender, field, value)

    await session.flush()
    await session.refresh(tender)
    new_state = _tender_to_dict(tender)

    # Log audit event
    await log_audit_event(
        session=session,
        action="TENDER_UPDATED",
        entity_type="tender",
        entity_id=str(tender.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state=prev_state,
        new_state=new_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()
    await session.refresh(tender)
    return tender


async def change_tender_status(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    new_status: TenderStatus,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tender:
    """Validate and transition tender lifecycle status."""
    tender = await get_tender_by_id(session, tender_id, organization_id)
    old_status = tender.status

    if old_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tender is already in '{new_status.value}' status.",
        )

    allowed = ALLOWED_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{old_status.value}' to '{new_status.value}'. Allowed transitions: {[s.value for s in allowed]}.",
        )

    prev_state = {"status": old_status.value}
    tender.status = new_status
    await session.flush()
    await session.refresh(tender)
    new_state = {"status": new_status.value}

    # Log audit event
    await log_audit_event(
        session=session,
        action="TENDER_STATUS_CHANGED",
        entity_type="tender",
        entity_id=str(tender.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state=prev_state,
        new_state=new_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()
    await session.refresh(tender)
    return tender


async def archive_tender(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tender:
    """Archive tender without physical deletion."""
    tender = await get_tender_by_id(session, tender_id, organization_id)

    if tender.status == TenderStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender is already archived.",
        )

    prev_state = {"status": tender.status.value}
    tender.status = TenderStatus.ARCHIVED
    await session.flush()
    await session.refresh(tender)
    new_state = {"status": TenderStatus.ARCHIVED.value}

    await log_audit_event(
        session=session,
        action="TENDER_ARCHIVED",
        entity_type="tender",
        entity_id=str(tender.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state=prev_state,
        new_state=new_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()
    await session.refresh(tender)
    return tender


async def delete_tender(
    session: AsyncSession,
    tender_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Physical deletion of a tender (strictly allowed only in DRAFT status)."""
    tender = await get_tender_by_id(session, tender_id, organization_id)

    if tender.status != TenderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete tender in '{tender.status.value}' status. Only DRAFT tenders may be physically deleted. Use archive instead.",
        )

    # 1. Capture snapshot and record audit event before deletion
    prev_state = _tender_to_dict(tender)
    await log_audit_event(
        session=session,
        action="TENDER_DELETED",
        entity_type="tender",
        entity_id=str(tender.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state=prev_state,
        new_state=None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.flush()

    # 2. Delete tender
    await session.delete(tender)
    await session.commit()
