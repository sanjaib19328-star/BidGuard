import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import DocumentProcessingStatus, TenderStatus

if TYPE_CHECKING:
    from app.models.user import Organization, User
    from app.models.clause import TenderClause
    from app.models.requirement import TenderRequirement
    from app.models.compliance_rule import ComplianceRule
    from app.models.compliance_evaluation import ComplianceEvaluation


class Tender(Base, TimestampMixin):
    __tablename__ = "tenders"
    __table_args__ = (
        UniqueConstraint("organization_id", "tender_number", name="uq_tenders_org_tender_number"),
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
    tender_number: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    procuring_entity: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    tender_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    source_portal: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    issue_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    submission_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    opening_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[TenderStatus] = mapped_column(
        Enum(TenderStatus, name="tender_status_enum", native_enum=True),
        nullable=False,
        default=TenderStatus.DRAFT,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="tenders",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    documents: Mapped[List["TenderDocument"]] = relationship(
        "TenderDocument",
        back_populates="tender",
        cascade="all, delete-orphan",
    )
    clauses: Mapped[List["TenderClause"]] = relationship(
        "TenderClause",
        back_populates="tender",
        cascade="all, delete-orphan",
    )
    requirements: Mapped[List["TenderRequirement"]] = relationship(
        "TenderRequirement",
        back_populates="tender",
        cascade="all, delete-orphan",
    )
    rules: Mapped[List["ComplianceRule"]] = relationship(
        "ComplianceRule",
        back_populates="tender",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[List["ComplianceEvaluation"]] = relationship(
        "ComplianceEvaluation",
        back_populates="tender",
        cascade="all, delete-orphan",
    )


class TenderDocument(Base, TimestampMixin):
    __tablename__ = "tender_documents"
    __table_args__ = (
        UniqueConstraint("tender_id", "sha256_hash", name="uq_tender_documents_tender_sha256"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="application/pdf",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    page_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(DocumentProcessingStatus, name="document_processing_status_enum", native_enum=True),
        nullable=False,
        default=DocumentProcessingStatus.UPLOADED,
        index=True,
    )
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(
        "Tender",
        back_populates="documents",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
    )
    uploader: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[uploaded_by],
    )
    pages: Mapped[List["TenderPage"]] = relationship(
        "TenderPage",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    clauses: Mapped[List["TenderClause"]] = relationship(
        "TenderClause",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class TenderPage(Base):
    __tablename__ = "tender_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    text_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["TenderDocument"] = relationship(
        "TenderDocument",
        back_populates="pages",
    )
    clauses: Mapped[List["TenderClause"]] = relationship(
        "TenderClause",
        back_populates="page",
    )
