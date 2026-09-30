from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DossierTenderInfo(BaseModel):
    id: str
    tender_number: str
    title: str
    description: Optional[str] = None
    status: str
    estimated_value: Optional[float] = None
    closing_date: Optional[str] = None


class DossierBidderInfo(BaseModel):
    id: str
    legal_name: str
    trade_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    udyam_number: Optional[str] = None
    is_mse: bool = False
    mse_category: Optional[str] = None
    asme_stamp_holder: bool = False
    asme_certificate_number: Optional[str] = None
    contact_email: Optional[str] = None
    registered_address: Optional[str] = None


class DossierMatrixItem(BaseModel):
    id: str
    dimension: Optional[str] = None
    status: str
    required_value: Optional[str] = None
    bidder_extracted_value: Optional[str] = None
    deviation_magnitude: Optional[float] = 0.0
    is_statutory: bool = False
    confidence_score: float = 0.0
    notes: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None


class DossierFindingItem(BaseModel):
    id: str
    severity: str
    finding_type: str
    title: str
    description: str
    recommended_action: Optional[str] = None
    review_status: str
    officer_notes: Optional[str] = None
    overridden_by: Optional[str] = None
    overridden_at: Optional[str] = None


class ComplianceDossierResponse(BaseModel):
    generated_at: str
    disclaimer: str
    tender: DossierTenderInfo
    bidder: DossierBidderInfo

    compliance_summary: Dict[str, Any]
    risk_profile: Dict[str, Any]
    evaluation_matrix_items: List[DossierMatrixItem]
    officer_findings: List[DossierFindingItem]
    statutory_verifications: List[Dict[str, Any]]
    mse_startup_assessment: Dict[str, Any]
    financial_eligibility: Dict[str, Any]
    technical_experience: Dict[str, Any]
    joint_venture_assessment: Dict[str, Any]
    debarment_integrity_check: Dict[str, Any]
    name_mismatch_analysis: List[Dict[str, Any]]
    clarifications_requested: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
    officer_action_block: Dict[str, Any]


class TenderDashboardMetrics(BaseModel):
    total_tenders: int
    active_tenders: int
    under_review_tenders: int
    completed_tenders: int
    archived_tenders: int


class BidderDashboardMetrics(BaseModel):
    total_bidders: int
    evaluated_bidders: int
    pending_bidders: int
    mse_bidders_count: int


class ComplianceMatrixDashboardMetrics(BaseModel):
    total_matrix_items: int
    compliant_count: int
    exempt_mse_count: int
    non_compliant_count: int
    partial_count: int = 0
    not_verifiable_count: int = 0
    overall_compliance_rate_percent: float


class RiskFindingsDashboardMetrics(BaseModel):
    total_findings: int
    unresolved_critical_high: int
    by_severity: Dict[str, int]
    by_review_status: Dict[str, int]


class VerificationDashboardMetrics(BaseModel):
    total_requests: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]


class DashboardActivityItem(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    created_at: Optional[str] = None


class DashboardMetricsResponse(BaseModel):
    generated_at: str
    disclaimer: str
    tender_metrics: TenderDashboardMetrics
    bidder_metrics: BidderDashboardMetrics
    compliance_matrix_metrics: ComplianceMatrixDashboardMetrics
    risk_findings_metrics: RiskFindingsDashboardMetrics
    verification_metrics: VerificationDashboardMetrics
    recent_activity: List[DashboardActivityItem]
