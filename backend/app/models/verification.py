import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ConnectorStatus,
    DataSourceType,
    NameMatchVerdict,
    VerificationResultStatus,
)

if TYPE_CHECKING:
    from app.models.bidder import Bidder
    from app.models.tender import Tender
    from app.models.user import Organization, User


class DataSourceConnector(Base, TimestampMixin):
    __tablename__ = "data_source_connectors"
    __table_args__ = (
        Index("ix_data_source_connectors_org_type", "organization_id", "source_type"),
        Index("ix_data_source_connectors_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType, name="data_source_type_enum", native_enum=True),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus, name="connector_status_enum", native_enum=True),
        default=ConnectorStatus.SANDBOX_ACTIVE,
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auth_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    last_health_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    requests: Mapped[List["VerificationRequest"]] = relationship("VerificationRequest", back_populates="connector")


class VerificationRequest(Base, TimestampMixin):
    __tablename__ = "verification_requests"
    __table_args__ = (
        Index("ix_verification_requests_bidder", "bidder_id"),
        Index("ix_verification_requests_tender", "tender_id"),
        Index("ix_verification_requests_type", "verification_type"),
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
    connector_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_source_connectors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    verification_type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType, name="data_source_type_enum", native_enum=True),
        nullable=False,
    )
    identifier_value: Mapped[str] = mapped_column(String(100), nullable=False)
    requested_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    bidder: Mapped["Bidder"] = relationship("Bidder")
    tender: Mapped[Optional["Tender"]] = relationship("Tender")
    connector: Mapped[Optional["DataSourceConnector"]] = relationship("DataSourceConnector", back_populates="requests")
    result: Mapped[Optional["VerificationResult"]] = relationship(
        "VerificationResult",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan",
    )


class VerificationResult(Base, TimestampMixin):
    __tablename__ = "verification_results"
    __table_args__ = (
        Index("ix_verification_results_bidder", "bidder_id"),
        Index("ix_verification_results_status", "status"),
        Index("ix_verification_results_verdict", "name_match_verdict"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    verification_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verification_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bidders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType, name="data_source_type_enum", native_enum=True),
        nullable=False,
    )
    status: Mapped[VerificationResultStatus] = mapped_column(
        Enum(VerificationResultStatus, name="verification_result_status_enum", native_enum=True),
        nullable=False,
    )
    sanitized_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sanitized external data stripped of secrets, auth headers, and tokens",
    )
    matched_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    name_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    name_match_verdict: Mapped[Optional[NameMatchVerdict]] = mapped_column(
        Enum(NameMatchVerdict, name="name_match_verdict_enum", native_enum=True),
        nullable=True,
    )
    discrepancies: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    officer_action_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    request: Mapped["VerificationRequest"] = relationship("VerificationRequest", back_populates="result")
    bidder: Mapped["Bidder"] = relationship("Bidder")
