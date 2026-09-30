import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import EvaluationStatus

if TYPE_CHECKING:
    from app.models.compliance_rule import ComplianceRule
    from app.models.requirement import TenderRequirement
    from app.models.tender import Tender


class ComplianceEvaluation(Base, TimestampMixin):
    __tablename__ = "compliance_evaluations"
    __table_args__ = (
        Index("ix_compliance_evals_tender_run", "tender_id", "evaluation_run_id"),
        Index("ix_compliance_evals_tender_status", "tender_id", "status"),
        Index("ix_compliance_evals_bidder", "tender_id", "bidder_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bidder_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, name="evaluation_status_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    actual_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    expected_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    evidence_reference: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    evaluator_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DETERMINISTIC_ENGINE",
    )
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(
        "Tender",
        back_populates="evaluations",
    )
    requirement: Mapped["TenderRequirement"] = relationship(
        "TenderRequirement",
        back_populates="evaluations",
    )
    rule: Mapped[Optional["ComplianceRule"]] = relationship(
        "ComplianceRule",
        back_populates="evaluations",
    )
