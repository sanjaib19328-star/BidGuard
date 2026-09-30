import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ClauseCategory,
    ComplianceRuleType,
    EvaluationStatus,
    RequirementApplicability,
    RequirementType,
    RiskHint,
    VerificationMethod,
)


class SourceRequirementMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: uuid.UUID
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
    verification_method: VerificationMethod
    risk_hint: RiskHint
    clause_number: Optional[str] = None
    page_number: Optional[int] = None


class ComplianceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    requirement_id: uuid.UUID
    rule_type: ComplianceRuleType
    rule_configuration: Dict[str, Any]
    description: str
    enabled: bool
    sequence_order: int
    confidence: float
    source_requirement: Optional[SourceRequirementMetadata] = None
    created_at: datetime
    updated_at: datetime


class ComplianceRuleListResponse(BaseModel):
    tender_id: uuid.UUID
    total: int
    page: int
    page_size: int
    rules_by_type: Dict[str, int]
    items: List[ComplianceRuleResponse]


class CompileRulesRequest(BaseModel):
    force_recompile: bool = Field(
        default=False,
        description="If True, re-compiles rules from current requirements and updates existing rules without destroying evaluation history.",
    )


class CompileRulesResponse(BaseModel):
    tender_id: uuid.UUID
    rules_created: int
    rules_updated: int
    rules_reused: int
    rules_total: int
    rules_by_type: Dict[str, int]
    status: str
    message: str


class EvaluateRulesRequest(BaseModel):
    bidder_id: Optional[str] = Field(
        default=None,
        description="Optional identifier or name for the bidder being evaluated",
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured bidder evidence payload (bidder_profile, financial, experience, documents, declarations, dates, attributes)",
    )


class EvaluationResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evaluation_id: uuid.UUID
    evaluation_run_id: uuid.UUID
    tender_id: uuid.UUID
    bidder_id: Optional[str] = None
    requirement_id: uuid.UUID
    rule_id: Optional[uuid.UUID] = None
    rule_type: Optional[ComplianceRuleType] = None
    status: EvaluationStatus
    actual_value: Optional[str] = None
    expected_value: Optional[str] = None
    evidence_reference: Optional[str] = None
    explanation: str
    mandatory: Optional[bool] = None
    risk_hint: Optional[RiskHint] = None
    evaluated_at: datetime
    source_requirement: Optional[SourceRequirementMetadata] = None


class EvaluationSummary(BaseModel):
    total: int
    passed: int
    failed: int
    partial: int
    not_verifiable: int
    not_applicable: int


class EvaluateRulesResponse(BaseModel):
    tender_id: uuid.UUID
    evaluation_run_id: uuid.UUID
    bidder_id: Optional[str] = None
    summary: EvaluationSummary
    results: List[EvaluationResultItem]
