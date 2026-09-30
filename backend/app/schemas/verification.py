import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ConnectorStatus,
    DataSourceType,
    NameMatchVerdict,
    VerificationResultStatus,
)


class ConnectorConfigureRequest(BaseModel):
    status: Optional[ConnectorStatus] = Field(None, description="Connector operating status")
    is_enabled: Optional[bool] = Field(None, description="Enable or disable connector")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Connector credentials & config")


class ConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    source_type: DataSourceType
    name: str
    description: Optional[str] = None
    status: ConnectorStatus
    is_enabled: bool
    auth_config: Optional[Dict[str, Any]] = None
    last_health_check_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ConnectorListResponse(BaseModel):
    items: List[ConnectorResponse]
    total: int


class ConnectorTestResponse(BaseModel):
    connector_id: str
    source_type: str
    status: str
    mode: str
    message: str


class SingleIdentifierVerificationRequest(BaseModel):
    source_type: DataSourceType = Field(..., description="Target data source (GSTN_PORTAL, UDYAM_MSME, CBDT_PAN)")
    identifier_value: str = Field(..., min_length=5, max_length=100, description="Identifier value (GSTIN, Udyam, or PAN)")
    bidder_id: Optional[uuid.UUID] = Field(None, description="Optional bidder UUID to attach result and match against legal name")
    tender_id: Optional[uuid.UUID] = Field(None, description="Optional tender UUID")


class GstVerificationRequest(BaseModel):
    gstin: str = Field(..., min_length=15, max_length=15, description="15-character GSTIN")
    bidder_id: Optional[uuid.UUID] = Field(None, description="Optional bidder UUID")
    tender_id: Optional[uuid.UUID] = Field(None, description="Optional tender UUID")


class UdyamVerificationRequest(BaseModel):
    udyam_number: str = Field(..., min_length=10, max_length=50, description="Udyam registration number")
    bidder_id: Optional[uuid.UUID] = Field(None, description="Optional bidder UUID")
    tender_id: Optional[uuid.UUID] = Field(None, description="Optional tender UUID")


class PanVerificationRequest(BaseModel):
    pan: str = Field(..., min_length=10, max_length=10, description="10-character permanent account number")
    bidder_id: Optional[uuid.UUID] = Field(None, description="Optional bidder UUID")
    tender_id: Optional[uuid.UUID] = Field(None, description="Optional tender UUID")


class BidderVerificationRunRequest(BaseModel):
    tender_id: Optional[uuid.UUID] = Field(None, description="Optional tender context for verification audit")


class VerificationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    verification_request_id: uuid.UUID
    bidder_id: uuid.UUID
    source_type: DataSourceType
    status: VerificationResultStatus
    sanitized_response: Optional[Dict[str, Any]] = None
    matched_fields: Optional[Dict[str, Any]] = None
    name_match_score: Optional[float] = None
    name_match_verdict: Optional[NameMatchVerdict] = None
    discrepancies: Optional[List[Dict[str, Any]]] = None
    officer_action_required: bool = False
    recommended_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BidderVerificationRunResponse(BaseModel):
    bidder_id: uuid.UUID
    bidder_legal_name: str
    overall_status: str
    total_checks: int
    results: List[VerificationResultResponse]


class VerificationResultListResponse(BaseModel):
    items: List[VerificationResultResponse]
    total: int
