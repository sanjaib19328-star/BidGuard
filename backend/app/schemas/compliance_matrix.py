from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    FindingReviewStatus,
    FindingSeverity,
    FindingType,
    MatrixItemStatus,
)


class EvaluationMatrixItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    compliance_rule_id: Optional[uuid.UUID] = None
    requirement_id: Optional[uuid.UUID] = None
    dimension: Optional[str] = None
    status: MatrixItemStatus
    required_value: Optional[str] = None
    bidder_extracted_value: Optional[str] = None
    deviation_magnitude: Optional[float] = None
    is_statutory: bool = False
    confidence_score: float = 1.0
    citations: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EvaluationMatrixResponse(BaseModel):
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    items: List[EvaluationMatrixItemResponse]
    total: int


class OfficerFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: uuid.UUID
    matrix_item_id: Optional[uuid.UUID] = None
    severity: FindingSeverity
    finding_type: FindingType
    title: str
    description: str
    evidence_data: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None
    review_status: FindingReviewStatus
    officer_notes: Optional[str] = None
    overridden_by_user_id: Optional[uuid.UUID] = None
    overridden_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OfficerFindingReviewRequest(BaseModel):
    review_status: FindingReviewStatus = Field(..., description="Action: ACCEPT, REJECT, OVERRIDE, CLARIFICATION_REQUESTED")
    officer_notes: Optional[str] = Field(None, description="Officer notes (Strictly required for OVERRIDE)")


class OfficerFindingListResponse(BaseModel):
    items: List[OfficerFindingResponse]
    summary: Dict[str, Any]


class BidderComparisonResponse(BaseModel):
    tender_id: str
    tender_title: str
    tender_number: str
    total_bidders_compared: int
    comparison_table: List[Dict[str, Any]]
    guardrail_notice: str
