import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    BidderDocumentType,
    DocumentProcessingStatus,
    EntityType,
    MseCategory,
    ParticipationStatus,
)

if TYPE_CHECKING:
    from app.models.tender import Tender
    from app.models.user import Organization


class Bidder(Base, TimestampMixin):
    __tablename__ = "bidders"
    __table_args__ = (
        Index("ix_bidders_org_legal_name", "organization_id", "legal_name"),
        Index("ix_bidders_gstin", "gstin"),
        Index("ix_bidders_pan", "pan"),
        Index("ix_bidders_udyam", "udyam_registration_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    udyam_registration_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registered_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    primary_contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Statutory flags
    is_mse: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mse_category: Mapped[MseCategory] = mapped_column(
        Enum(MseCategory, name="mse_category_enum", native_enum=True),
        default=MseCategory.NOT_APPLICABLE,
        nullable=False,
    )
    asme_stamp_holder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    asme_certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    documents: Mapped[List["BidderDocument"]] = relationship(
        "BidderDocument",
        back_populates="bidder",
        cascade="all, delete-orphan",
        order_by="BidderDocument.created_at.desc()",
    )
    participations: Mapped[List["BidderTenderParticipation"]] = relationship(
        "BidderTenderParticipation",
        back_populates="bidder",
        cascade="all, delete-orphan",
    )
    extracted_entities: Mapped[List["ExtractedEntity"]] = relationship(
        "ExtractedEntity",
        back_populates="bidder",
        cascade="all, delete-orphan",
    )


class BidderTenderParticipation(Base, TimestampMixin):
    __tablename__ = "bidder_tender_participations"
    __table_args__ = (
        Index("ix_bidder_tender_part", "bidder_id", "tender_id", unique=True),
        Index("ix_bidder_part_status", "tender_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ParticipationStatus] = mapped_column(
        Enum(ParticipationStatus, name="participation_status_enum", native_enum=True),
        default=ParticipationStatus.DRAFT,
        nullable=False,
    )
    submission_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    officer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="participations")
    tender: Mapped["Tender"] = relationship("Tender")


class BidderDocument(Base, TimestampMixin):
    __tablename__ = "bidder_documents"
    __table_args__ = (
        Index("ix_bidder_docs_bidder", "bidder_id"),
        Index("ix_bidder_docs_tender", "tender_id"),
        Index("ix_bidder_docs_type", "bidder_id", "document_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tender_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_type: Mapped[BidderDocumentType] = mapped_column(
        Enum(BidderDocumentType, name="bidder_document_type_enum", native_enum=True),
        default=BidderDocumentType.OTHER,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(DocumentProcessingStatus, name="document_processing_status_enum", native_enum=True),
        default=DocumentProcessingStatus.UPLOADED,
        nullable=False,
    )
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="documents")
    pages: Mapped[List["BidderDocumentPage"]] = relationship(
        "BidderDocumentPage",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="BidderDocumentPage.page_number.asc()",
    )
    extracted_entities: Mapped[List["ExtractedEntity"]] = relationship(
        "ExtractedEntity",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class BidderDocumentPage(Base, TimestampMixin):
    __tablename__ = "bidder_document_pages"
    __table_args__ = (
        Index("ix_bidder_doc_pages_doc_page", "document_id", "page_number", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidder_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    has_tables: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extracted_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    document: Mapped["BidderDocument"] = relationship("BidderDocument", back_populates="pages")


class ExtractedEntity(Base, TimestampMixin):
    __tablename__ = "extracted_entities"
    __table_args__ = (
        Index("ix_extracted_entities_bidder", "bidder_id"),
        Index("ix_extracted_entities_doc", "document_id"),
        Index("ix_extracted_entities_type", "bidder_id", "entity_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidder_documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type_enum", native_enum=True),
        nullable=False,
    )
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    context_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    bidder: Mapped["Bidder"] = relationship("Bidder", back_populates="extracted_entities")
    document: Mapped[Optional["BidderDocument"]] = relationship("BidderDocument", back_populates="extracted_entities")
