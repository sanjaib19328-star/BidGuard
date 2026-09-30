import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ComplianceRuleType

if TYPE_CHECKING:
    from app.models.compliance_evaluation import ComplianceEvaluation
    from app.models.requirement import TenderRequirement
    from app.models.tender import Tender


class ComplianceRule(Base, TimestampMixin):
    __tablename__ = "compliance_rules"
    __table_args__ = (
        Index("ix_compliance_rules_tender_type", "tender_id", "rule_type"),
        Index("ix_compliance_rules_tender_seq", "tender_id", "sequence_order"),
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
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[ComplianceRuleType] = mapped_column(
        Enum(ComplianceRuleType, name="compliance_rule_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    rule_configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(
        "Tender",
        back_populates="rules",
    )
    requirement: Mapped["TenderRequirement"] = relationship(
        "TenderRequirement",
        back_populates="rules",
    )
    evaluations: Mapped[List["ComplianceEvaluation"]] = relationship(
        "ComplianceEvaluation",
        back_populates="rule",
    )
