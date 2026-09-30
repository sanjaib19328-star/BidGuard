import hashlib
import os
from pathlib import Path
from typing import List, Optional, Tuple
import uuid
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.bidder import Bidder, BidderDocument, BidderDocumentPage
from app.models.enums import BidderDocumentType, DocumentProcessingStatus
from app.services import storage_service
from app.services.audit_service import log_audit_event
from app.services.bidder_service import get_bidder_by_id

CHUNK_SIZE = 64 * 1024


def get_bidder_upload_dir(bidder_id: uuid.UUID) -> Path:
    """Get directory for bidder document storage."""
    base_dir = storage_service.get_base_upload_dir()
    bidder_dir = base_dir / "bidders" / str(bidder_id)
    bidder_dir.mkdir(parents=True, exist_ok=True)
    return bidder_dir


def delete_bidder_directory(bidder_id: uuid.UUID) -> bool:
    """Safely delete all documents and directory for a bidder."""
    import shutil
    try:
        base_dir = storage_service.get_base_upload_dir()
        bidder_dir = base_dir / "bidders" / str(bidder_id)
        if bidder_dir.is_dir():
            shutil.rmtree(bidder_dir, ignore_errors=True)
            return True
    except Exception:
        pass
    return False


async def upload_bidder_document(
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    bidder_id: uuid.UUID,
    upload_file: UploadFile,
    document_type: BidderDocumentType = BidderDocumentType.OTHER,
    tender_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> BidderDocument:
    """Upload and store a PDF document for a bidder with SHA-256 deduplication."""
    # 1. Verify bidder exists
    await get_bidder_by_id(session, bidder_id, organization_id)

    original_filename = upload_file.filename or "document.pdf"
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files (.pdf) are allowed.",
        )

    # 2. Prepare target file path
    bidder_dir = get_bidder_upload_dir(bidder_id)
    doc_uuid = uuid.uuid4()
    safe_filename = f"{doc_uuid}.pdf"
    target_path = bidder_dir / safe_filename

    max_size_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    hasher = hashlib.sha256()
    bytes_written = 0
    first_chunk = True

    try:
        with open(target_path, "wb") as f_out:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break

                if first_chunk:
                    first_chunk = False
                    if not chunk.startswith(b"%PDF-"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid PDF content: file header does not match PDF signature (%PDF-).",
                        )

                bytes_written += len(chunk)
                if bytes_written > max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed limit of {settings.MAX_DOCUMENT_SIZE_MB}MB.",
                    )

                hasher.update(chunk)
                f_out.write(chunk)

        if bytes_written == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

    except Exception:
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                pass
        raise

    sha256_hash = hasher.hexdigest()
    storage_path = str(target_path)

    try:
        # 3. Duplicate check for this bidder
        dup_query = select(BidderDocument).where(
            BidderDocument.bidder_id == bidder_id,
            BidderDocument.sha256_hash == sha256_hash,
        )
        dup_res = await session.execute(dup_query)
        if dup_res.scalar_one_or_none():
            storage_service.delete_file(storage_path)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document with identical content (SHA-256: {sha256_hash}) has already been uploaded for this bidder.",
            )

        # 4. Insert DB record
        doc = BidderDocument(
            id=doc_uuid,
            bidder_id=bidder_id,
            tender_id=tender_id,
            document_type=document_type,
            filename=safe_filename,
            original_filename=original_filename,
            storage_path=storage_path,
            mime_type="application/pdf",
            file_size=bytes_written,
            sha256_hash=sha256_hash,
            processing_status=DocumentProcessingStatus.UPLOADED,
        )
        session.add(doc)
        await session.flush()
        await session.refresh(doc)

        await log_audit_event(
            session=session,
            action="BIDDER_DOCUMENT_UPLOADED",
            entity_type="bidder_document",
            entity_id=str(doc.id),
            organization_id=organization_id,
            actor_user_id=user_id,
            new_state={"filename": original_filename, "doc_type": document_type.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await session.commit()
        await session.refresh(doc)
        return doc

    except Exception:
        storage_service.delete_file(storage_path)
        raise


async def list_bidder_documents(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    organization_id: uuid.UUID,
    document_type: Optional[BidderDocumentType] = None,
) -> Tuple[List[BidderDocument], int]:
    """List documents for a bidder."""
    await get_bidder_by_id(session, bidder_id, organization_id)
    query = select(BidderDocument).where(BidderDocument.bidder_id == bidder_id)
    if document_type:
        query = query.where(BidderDocument.document_type == document_type)
    query = query.order_by(BidderDocument.created_at.desc())
    res = await session.execute(query)
    docs = list(res.scalars().all())
    return docs, len(docs)


async def get_bidder_document(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    document_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> BidderDocument:
    """Retrieve metadata for a single bidder document."""
    await get_bidder_by_id(session, bidder_id, organization_id)
    query = select(BidderDocument).where(
        BidderDocument.id == document_id,
        BidderDocument.bidder_id == bidder_id,
    )
    res = await session.execute(query)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder document not found.",
        )
    return doc


async def get_bidder_document_for_download(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    document_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Tuple[Path, str, str]:
    """Get file path, original filename, and MIME type for download."""
    doc = await get_bidder_document(session, bidder_id, document_id, organization_id)
    if not storage_service.file_exists(doc.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical document file not found on storage server.",
        )
    return Path(doc.storage_path), doc.original_filename, doc.mime_type


async def delete_bidder_document(
    session: AsyncSession,
    bidder_id: uuid.UUID,
    document_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Delete a bidder document and its physical storage file."""
    doc = await get_bidder_document(session, bidder_id, document_id, organization_id)
    storage_path = doc.storage_path

    await log_audit_event(
        session=session,
        action="BIDDER_DOCUMENT_DELETED",
        entity_type="bidder_document",
        entity_id=str(doc.id),
        organization_id=organization_id,
        actor_user_id=user_id,
        previous_state={"filename": doc.original_filename},
        new_state=None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await session.delete(doc)
    await session.commit()
    storage_service.delete_file(storage_path)


async def ensure_bidder_pages_extracted(
    session: AsyncSession,
    document: BidderDocument,
) -> List[BidderDocumentPage]:
    """Extract pages and text from bidder PDF on disk into BidderDocumentPage records."""
    # 1. Check if pages already extracted
    query = (
        select(BidderDocumentPage)
        .where(BidderDocumentPage.document_id == document.id)
        .order_by(BidderDocumentPage.page_number.asc())
    )
    res = await session.execute(query)
    existing = list(res.scalars().all())
    if existing:
        return existing

    if not storage_service.file_exists(document.storage_path):
        document.processing_status = DocumentProcessingStatus.FAILED
        await session.flush()
        return []

    document.processing_status = DocumentProcessingStatus.PROCESSING
    await session.flush()

    pages: List[BidderDocumentPage] = []
    try:
        import pypdf
        reader = pypdf.PdfReader(document.storage_path)
        for idx, p in enumerate(reader.pages, start=1):
            text = p.extract_text() or ""
            page_obj = BidderDocumentPage(
                document_id=document.id,
                page_number=idx,
                text_content=text,
                has_tables="|" in text or "\t" in text,
            )
            session.add(page_obj)
            pages.append(page_obj)

        if not pages:
            page_obj = BidderDocumentPage(
                document_id=document.id,
                page_number=1,
                text_content="",
            )
            session.add(page_obj)
            pages.append(page_obj)

        document.page_count = len(pages)
        document.processing_status = DocumentProcessingStatus.PROCESSED
        await session.flush()
        return pages

    except Exception:
        document.processing_status = DocumentProcessingStatus.FAILED
        await session.flush()
        return []
