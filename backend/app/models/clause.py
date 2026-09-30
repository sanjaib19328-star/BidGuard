import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ClauseCategory

if TYPE_CHECKING:
    from app.models.tender import Tender, TenderDocument, TenderPage
    from app.models.requirement import TenderRequirement


class TenderClause(Base, TimestampMixin):
    __tablename__ = "tender_clauses"
    __table_args__ = (
        Index("ix_tender_clauses_tender_category", "tender_id", "category"),
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
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_pages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    clause_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    clause_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category: Mapped[ClauseCategory] = mapped_column(
        Enum(ClauseCategory, name="clause_category_enum", native_enum=True),
        nullable=False,
        default=ClauseCategory.GENERAL,
        index=True,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    extraction_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RULE_BASED",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(
        "Tender",
        back_populates="clauses",
    )
    document: Mapped["TenderDocument"] = relationship(
        "TenderDocument",
        back_populates="clauses",
    )
    page: Mapped[Optional["TenderPage"]] = relationship(
        "TenderPage",
        back_populates="clauses",
    )
    requirements: Mapped[List["TenderRequirement"]] = relationship(
        "TenderRequirement",
        back_populates="clause",
        cascade="all, delete-orphan",
    )
