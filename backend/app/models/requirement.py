import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ClauseCategory,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    VerificationMethod,
)

if TYPE_CHECKING:
    from app.models.clause import TenderClause
    from app.models.tender import Tender
    from app.models.compliance_rule import ComplianceRule
    from app.models.compliance_evaluation import ComplianceEvaluation


class TenderRequirement(Base, TimestampMixin):
    __tablename__ = "tender_requirements"
    __table_args__ = (
        Index("ix_tender_requirements_tender_category", "tender_id", "category"),
        Index("ix_tender_requirements_tender_type", "tender_id", "requirement_type"),
        Index("ix_tender_requirements_tender_signature", "tender_id", "requirement_signature"),
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
    clause_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_clauses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[ClauseCategory] = mapped_column(
        Enum(ClauseCategory, name="clause_category_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    requirement_type: Mapped[RequirementType] = mapped_column(
        Enum(RequirementType, name="requirement_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    operator: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    value_numeric: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    value_text: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    currency: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    period: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    mandatory: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        default=True,
        index=True,
    )
    applicability: Mapped[RequirementApplicability] = mapped_column(
        Enum(RequirementApplicability, name="requirement_applicability_enum", native_enum=True),
        nullable=False,
        default=RequirementApplicability.ALL_BIDDERS,
        index=True,
    )
    applicability_condition: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    required_evidence: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    verification_method: Mapped[VerificationMethod] = mapped_column(
        Enum(VerificationMethod, name="verification_method_enum", native_enum=True),
        nullable=False,
        default=VerificationMethod.DOCUMENT,
        index=True,
    )
    risk_hint: Mapped[RiskHint] = mapped_column(
        Enum(RiskHint, name="risk_hint_enum", native_enum=True),
        nullable=False,
        default=RiskHint.MEDIUM,
        index=True,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )
    extraction_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RULE_BASED",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.90,
    )
    requirement_signature: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(
        "Tender",
        back_populates="requirements",
    )
    clause: Mapped["TenderClause"] = relationship(
        "TenderClause",
        back_populates="requirements",
    )
    rules: Mapped[List["ComplianceRule"]] = relationship(
        "ComplianceRule",
        back_populates="requirement",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[List["ComplianceEvaluation"]] = relationship(
        "ComplianceEvaluation",
        back_populates="requirement",
        cascade="all, delete-orphan",
    )

