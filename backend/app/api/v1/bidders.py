import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.models.bidder import ExtractedEntity
from app.models.enums import BidderDocumentType, UserRole
from app.models.user import User
from app.schemas.bidder import (
    BidderCreateRequest,
    BidderDocumentListResponse,
    BidderDocumentResponse,
    BidderListResponse,
    BidderProfileSummaryResponse,
    BidderResponse,
    BidderTenderParticipationCreateRequest,
    BidderTenderParticipationResponse,
    BidderUpdateRequest,
    DocumentExtractRunResponse,
    ExtractedEntityListResponse,
    ExtractedEntityResponse,
)
from app.services import (
    bidder_document_service,
    bidder_intelligence_service,
    bidder_service,
)

router = APIRouter(prefix="/bidders", tags=["Bidders"])


@router.post(
    "",
    response_model=BidderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bidder profile",
)
async def create_bidder(
    data: BidderCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    bidder = await bidder_service.create_bidder(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
        ip_address=ip,
        user_agent=ua,
    )
    return BidderResponse.model_validate(bidder)


@router.get(
    "",
    response_model=BidderListResponse,
    summary="List all bidders for organization",
)
async def list_bidders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, GSTIN, PAN"),
    tender_id: Optional[uuid.UUID] = Query(None, description="Filter by tender participation"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bidders, total = await bidder_service.list_bidders(
        session=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        tender_id=tender_id,
    )
    return BidderListResponse(
        bidders=[BidderResponse.model_validate(b) for b in bidders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{bidder_id}",
    response_model=BidderProfileSummaryResponse,
    summary="Get unified bidder profile summary",
)
async def get_bidder_profile(
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = await bidder_service.get_bidder_profile_summary(
        session=db,
        bidder_id=bidder_id,
        organization_id=current_user.organization_id,
    )
    return summary


@router.put(
    "/{bidder_id}",
    response_model=BidderResponse,
    summary="Update bidder details",
)
async def update_bidder(
    bidder_id: uuid.UUID,
    data: BidderUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    bidder = await bidder_service.update_bidder(
        session=db,
        bidder_id=bidder_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
        ip_address=ip,
        user_agent=ua,
    )
    return BidderResponse.model_validate(bidder)


@router.delete(
    "/{bidder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bidder",
)
async def delete_bidder(
    bidder_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await bidder_service.delete_bidder(
        session=db,
        bidder_id=bidder_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


# ==============================================================================
# Document Management Endpoints
# ==============================================================================

@router.post(
    "/{bidder_id}/documents",
    response_model=BidderDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for a bidder",
)
async def upload_bidder_document(
    bidder_id: uuid.UUID,
    file: UploadFile = File(...),
    document_type: BidderDocumentType = Form(BidderDocumentType.OTHER),
    tender_id: Optional[uuid.UUID] = Form(None),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    ip = request.client.host if request and request.client else None
    ua = request.headers.get("user-agent") if request else None
    doc = await bidder_document_service.upload_bidder_document(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        bidder_id=bidder_id,
        upload_file=file,
        document_type=document_type,
        tender_id=tender_id,
        ip_address=ip,
        user_agent=ua,
    )
    return BidderDocumentResponse.model_validate(doc)


@router.get(
    "/{bidder_id}/documents",
    response_model=BidderDocumentListResponse,
    summary="List all documents for a bidder",
)
async def list_bidder_documents(
    bidder_id: uuid.UUID,
    document_type: Optional[BidderDocumentType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs, total = await bidder_document_service.list_bidder_documents(
        session=db,
        bidder_id=bidder_id,
        organization_id=current_user.organization_id,
        document_type=document_type,
    )
    return BidderDocumentListResponse(
        documents=[BidderDocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


@router.get(
    "/{bidder_id}/documents/{doc_id}",
    response_model=BidderDocumentResponse,
    summary="Get bidder document metadata",
)
async def get_bidder_document(
    bidder_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await bidder_document_service.get_bidder_document(
        session=db,
        bidder_id=bidder_id,
        document_id=doc_id,
        organization_id=current_user.organization_id,
    )
    return BidderDocumentResponse.model_validate(doc)


@router.get(
    "/{bidder_id}/documents/{doc_id}/download",
    summary="Download bidder document binary file",
)
async def download_bidder_document(
    bidder_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path, filename, mime_type = await bidder_document_service.get_bidder_document_for_download(
        session=db,
        bidder_id=bidder_id,
        document_id=doc_id,
        organization_id=current_user.organization_id,
    )
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=mime_type,
    )


@router.delete(
    "/{bidder_id}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bidder document",
)
async def delete_bidder_document(
    bidder_id: uuid.UUID,
    doc_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await bidder_document_service.delete_bidder_document(
        session=db,
        bidder_id=bidder_id,
        document_id=doc_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


# ==============================================================================
# Document Intelligence & Extraction Endpoints
# ==============================================================================

@router.post(
    "/{bidder_id}/documents/{doc_id}/extract",
    response_model=DocumentExtractRunResponse,
    summary="Run AI classification & entity extraction on bidder document",
)
async def extract_bidder_document(
    bidder_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    classified_type, conf, entities = await bidder_intelligence_service.extract_and_classify_bidder_document(
        session=db,
        bidder_id=bidder_id,
        document_id=doc_id,
        organization_id=current_user.organization_id,
    )
    doc = await bidder_document_service.get_bidder_document(
        session=db,
        bidder_id=bidder_id,
        document_id=doc_id,
        organization_id=current_user.organization_id,
    )
    return DocumentExtractRunResponse(
        document_id=doc_id,
        classified_type=classified_type,
        confidence=conf,
        pages_processed=doc.page_count,
        extracted_entities_count=len(entities),
        entities=[ExtractedEntityResponse.model_validate(e) for e in entities],
    )


@router.get(
    "/{bidder_id}/entities",
    response_model=ExtractedEntityListResponse,
    summary="List all extracted entities for bidder",
)
async def list_bidder_entities(
    bidder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await bidder_service.get_bidder_by_id(db, bidder_id, current_user.organization_id)
    query = select(ExtractedEntity).where(ExtractedEntity.bidder_id == bidder_id).order_by(ExtractedEntity.created_at.asc())
    res = await db.execute(query)
    entities = list(res.scalars().all())
    return ExtractedEntityListResponse(
        entities=[ExtractedEntityResponse.model_validate(e) for e in entities],
        total=len(entities),
    )


@router.post(
    "/{bidder_id}/participate",
    response_model=BidderTenderParticipationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record or update bidder tender participation",
)
async def record_participation(
    bidder_id: uuid.UUID,
    data: BidderTenderParticipationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER])),
):
    part = await bidder_service.record_tender_participation(
        session=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        bidder_id=bidder_id,
        data=data,
    )
    return BidderTenderParticipationResponse.model_validate(part)
