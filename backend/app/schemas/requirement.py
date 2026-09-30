import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ClauseCategory,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    VerificationMethod,
)


class SourceClauseMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clause_id: uuid.UUID
    clause_number: Optional[str] = None
    title: Optional[str] = None
    page_number: int
    document_id: uuid.UUID


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    clause_id: uuid.UUID
    category: ClauseCategory
    requirement_type: RequirementType
    description: str
    operator: Optional[str] = None
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    mandatory: Optional[bool] = None
    applicability: RequirementApplicability
    applicability_condition: Optional[str] = None
    required_evidence: List[str]
    verification_method: VerificationMethod
    risk_hint: RiskHint
    sequence_order: int
    extraction_method: str
    confidence: float
    source: Optional[SourceClauseMetadata] = None
    created_at: datetime
    updated_at: datetime


class RequirementListResponse(BaseModel):
    items: List[RequirementResponse]
    total: int
    page: int
    page_size: int
    tender_id: uuid.UUID
    categories_breakdown: Dict[str, int]
    types_breakdown: Dict[str, int]


class RequirementExtractionRequest(BaseModel):
    force_reextract: bool = Field(
        default=False,
        description="Whether to overwrite and atomically re-extract requirements for this tender",
    )


class RequirementExtractionResponse(BaseModel):
    tender_id: uuid.UUID
    requirements_created: int
    requirements_reused: int
    requirements_total: int
    categories_breakdown: Dict[str, int]
    types_breakdown: Dict[str, int]
    status: str
    message: str
