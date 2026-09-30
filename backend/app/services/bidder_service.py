import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bidder import Bidder, BidderDocument, BidderTenderParticipation, ExtractedEntity
from app.models.enums import ParticipationStatus
from app.models.tender import Tender
from app.schemas.bidder import (
    BidderCreateRequest,
    BidderProfileSummaryResponse,
    BidderResponse,
    BidderTenderParticipationCreateRequest,
    BidderTenderParticipationResponse,
    BidderUpdateRequest,
)
from app.services.audit_service import log_audit_event


async def create_bidder(
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    data: BidderCreateRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Bidder:
    """Create a new bidder under the organization with duplicate validation."""
    # 1. Check for duplicate legal name or GSTIN within organization
    query = select(Bidder).where(
        Bidder.organization_id == organization_id,
        or_(
            func.lower(Bidder.legal_name) == data.legal_name.strip().lower(),
            (Bidder.gstin == data.gstin.strip().upper()) if data.gstin else False,
        ),
    )
    res = await session.execute(query)
    existing = res.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bidder with name '{data.legal_name}' or GSTIN '{data.gstin}' already exists.",
        )

    # 2. Instantiate Bidder
    bidder = Bidder(
        organization_id=organization_id,
        legal_name=data.legal_name.strip(),
        trade_name=data.trade_name.strip() if data.trade_name else None,
        gstin=data.gstin.strip().upper() if data.gstin else None,
        pan=data.pan.strip().upper() if data.pan else None,
        udyam_registration_number=data.udyam_registration_number.strip().upper() if data.udyam_registration_number else None,
        registered_address=data.registered_address,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        primary_contact_person=data.primary_contact_person,
        is_mse=data.is_mse,
        mse_category=data.mse_category,
        asme_stamp_holder=data.asme_stamp_holder,
        asme_certificate_number=data.asme_certificate_number,
    )
    session.add(bidder)
    await session.flush()
    await session.refresh(bidder)

    # 3. Log audit event
    await log_audit_event(
        session=session,
        action="BIDDER_CREATED",
        entity_type="bidder",
        entity_id=str(bidder.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        new_state={"legal_name": bidder.legal_name, "gstin": bidder.gstin},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()
    await session.refresh(bidder)
    return bidder


async def get_bidder_by_id(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Bidder:
    """Retrieve single bidder scoped to organization."""
    query = select(Bidder).where(
        Bidder.id == bidder_id,
        Bidder.organization_id == organization_id,
    )
    res = await session.execute(query)
    bidder = res.scalar_one_or_none()
    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found.",
        )
    return bidder


async def list_bidders(
    session: AsyncSession,
    organization_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    tender_id: Optional[uuid.UUID] = None,
) -> Tuple[List[Bidder], int]:
    """List bidders with filtering and pagination."""
    query = select(Bidder).where(Bidder.organization_id == organization_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Bidder.legal_name.ilike(term),
                Bidder.trade_name.ilike(term),
                Bidder.gstin.ilike(term),
                Bidder.pan.ilike(term),
                Bidder.udyam_registration_number.ilike(term),
            )
        )

    if tender_id:
        query = query.join(BidderTenderParticipation, BidderTenderParticipation.bidder_id == Bidder.id).where(
            BidderTenderParticipation.tender_id == tender_id
        )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await session.execute(count_query)
    total = total_res.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Bidder.legal_name.asc()).offset(offset).limit(page_size)
    items_res = await session.execute(query)
    bidders = list(items_res.scalars().all())

    return bidders, total


async def update_bidder(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    data: BidderUpdateRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Bidder:
    """Update bidder fields."""
    bidder = await get_bidder_by_id(session, bidder_id, organization_id)
    prev_state = {"legal_name": bidder.legal_name, "gstin": bidder.gstin}

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        if isinstance(val, str):
            val = val.strip()
        setattr(bidder, field, val)

    await session.flush()
    await log_audit_event(
        session=session,
        action="BIDDER_UPDATED",
        entity_type="bidder",
        entity_id=str(bidder.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state=prev_state,
        new_state={"legal_name": bidder.legal_name, "gstin": bidder.gstin},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.commit()
    await session.refresh(bidder)
    return bidder


async def delete_bidder(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Delete bidder and cascade."""
    bidder = await get_bidder_by_id(session, bidder_id, organization_id)
    await log_audit_event(
        session=session,
        action="BIDDER_DELETED",
        entity_type="bidder",
        entity_id=str(bidder.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state={"legal_name": bidder.legal_name},
        new_state=None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.delete(bidder)
    await session.commit()


async def record_tender_participation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    bidder_id: uuid.UUID,
    data: BidderTenderParticipationCreateRequest,
) -> BidderTenderParticipation:
    """Associate a bidder with a specific tender submission."""
    # Verify bidder exists
    await get_bidder_by_id(session, bidder_id, organization_id)

    # Verify tender exists
    t_query = select(Tender).where(Tender.id == data.tender_id, Tender.organization_id == organization_id)
    t_res = await session.execute(t_query)
    if not t_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    # Check existing participation
    p_query = select(BidderTenderParticipation).where(
        BidderTenderParticipation.bidder_id == bidder_id,
        BidderTenderParticipation.tender_id == data.tender_id,
    )
    p_res = await session.execute(p_query)
    existing = p_res.scalar_one_or_none()
    if existing:
        existing.status = data.status
        if data.submission_date:
            existing.submission_date = data.submission_date
        if data.officer_notes:
            existing.officer_notes = data.officer_notes
        await session.commit()
        await session.refresh(existing)
        return existing

    part = BidderTenderParticipation(
        bidder_id=bidder_id,
        tender_id=data.tender_id,
        status=data.status,
        submission_date=data.submission_date,
        officer_notes=data.officer_notes,
    )
    session.add(part)
    await session.commit()
    await session.refresh(part)
    return part


async def get_bidder_profile_summary(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> BidderProfileSummaryResponse:
    """Retrieve comprehensive profile summary with count stats."""
    bidder = await get_bidder_by_id(session, bidder_id, organization_id)

    # Document count
    doc_count_res = await session.execute(
        select(func.count()).select_from(BidderDocument).where(BidderDocument.bidder_id == bidder_id)
    )
    docs_count = doc_count_res.scalar_one()

    # Entity count
    ent_count_res = await session.execute(
        select(func.count()).select_from(ExtractedEntity).where(ExtractedEntity.bidder_id == bidder_id)
    )
    ent_count = ent_count_res.scalar_one()

    # Participations
    parts_res = await session.execute(
        select(BidderTenderParticipation)
        .where(BidderTenderParticipation.bidder_id == bidder_id)
        .order_by(BidderTenderParticipation.created_at.desc())
    )
    participations = list(parts_res.scalars().all())

    return BidderProfileSummaryResponse(
        bidder=BidderResponse.model_validate(bidder),
        documents_count=docs_count,
        participations_count=len(participations),
        extracted_entities_count=ent_count,
        participations=[BidderTenderParticipationResponse.model_validate(p) for p in participations],
    )
