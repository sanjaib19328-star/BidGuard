import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
)

if TYPE_CHECKING:
    from app.models.bidder import Bidder
    from app.models.compliance import ComplianceRule
    from app.models.requirement import TenderRequirement
    from app.models.tender import Tender
    from app.models.user import User


class EvaluationMatrixItem(Base, TimestampMixin):
    """Multi-dimensional compliance evaluation matrix item mapping a requirement/rule to a bidder's evidence."""
    __tablename__ = "evaluation_matrix_items"
    __table_args__ = (
        Index("ix_matrix_tender_bidder", "tender_id", "bidder_id"),
        Index("ix_matrix_status", "status"),
        Index("ix_matrix_rule", "compliance_rule_id"),
        Index("ix_matrix_req", "requirement_id"),
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
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    compliance_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )

    dimension: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[MatrixItemStatus] = mapped_column(
        Enum(MatrixItemStatus, name="matrix_item_status_enum", native_enum=True),
        nullable=False,
        default=MatrixItemStatus.NOT_VERIFIABLE,
    )
    required_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bidder_extracted_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deviation_magnitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_statutory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    citations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Structured evidence citations (document_id, page, snippet, source_type)",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    tender: Mapped["Tender"] = relationship("Tender")
    bidder: Mapped["Bidder"] = relationship("Bidder")
    compliance_rule: Mapped[Optional["ComplianceRule"]] = relationship("ComplianceRule")
    requirement: Mapped[Optional["TenderRequirement"]] = relationship("TenderRequirement")
    findings: Mapped[List["OfficerFinding"]] = relationship("OfficerFinding", back_populates="matrix_item")


class OfficerFinding(Base, TimestampMixin):
    """Procurement officer findings requiring evaluation, justification, override, or clarification."""
    __tablename__ = "officer_findings"
    __table_args__ = (
        Index("ix_officer_findings_tender_bidder", "tender_id", "bidder_id"),
        Index("ix_officer_findings_severity", "severity"),
        Index("ix_officer_findings_status", "review_status"),
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
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matrix_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_matrix_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity_enum", native_enum=True),
        nullable=False,
        default=FindingSeverity.MEDIUM,
    )
    finding_type: Mapped[FindingType] = mapped_column(
        Enum(FindingType, name="finding_type_enum", native_enum=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Context evidence: tender clause page, bidder doc page, verification payload",
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Review workflow
    review_status: Mapped[FindingReviewStatus] = mapped_column(
        Enum(FindingReviewStatus, name="finding_review_status_enum", native_enum=True),
        default=FindingReviewStatus.PENDING,
        nullable=False,
    )
    officer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overridden_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    overridden_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tender: Mapped["Tender"] = relationship("Tender")
    bidder: Mapped["Bidder"] = relationship("Bidder")
    matrix_item: Mapped[Optional["EvaluationMatrixItem"]] = relationship("EvaluationMatrixItem", back_populates="findings")
    overridden_by_user: Mapped[Optional["User"]] = relationship("User")
