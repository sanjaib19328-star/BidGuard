export type ClauseCategory = 
  | 'STATUTORY'
  | 'FINANCIAL'
  | 'TECHNICAL'
  | 'COMMERCIAL'
  | 'ELIGIBILITY'
  | 'SUBMISSION'
  | 'ADMINISTRATIVE'
  | 'GENERAL';

export type MatrixItemStatus = 
  | 'COMPLIANT'
  | 'NON_COMPLIANT'
  | 'CONDITIONAL'
  | 'EXEMPT_MSE'
  | 'EXEMPT_STARTUP'
  | 'REVIEW';

export type FindingSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type FindingReviewStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'OVERRIDDEN' | 'CLARIFICATION_REQUESTED';

export type VerificationStatus = 'VERIFIED' | 'FAILED' | 'MISMATCH' | 'PENDING' | 'EXEMPT';

export interface Tender {
  id: string;
  tender_number: string;
  title: string;
  issuing_authority: string;
  ministry?: string;
  estimated_value?: number;
  estimated_value_display?: string;
  emd_amount?: number;
  turnover_requirement_lakhs?: number;
  past_experience_years?: number;
  mse_exemption_permitted: boolean;
  startup_exemption_permitted: boolean;
  status: 'DRAFT' | 'UNDER_REVIEW' | 'VERIFIED' | 'COMPLETED';
  created_at: string;
  total_clauses?: number;
  total_requirements?: number;
}

export interface Clause {
  id: string;
  clause_number?: string;
  title?: string;
  category: ClauseCategory;
  clause_text: string;
  page_number: number;
  confidence_score: number;
  requirements_count?: number;
}

export interface Requirement {
  id: string;
  clause_id: string;
  category: ClauseCategory;
  requirement_type: string;
  description: string;
  operator?: string;
  target_value?: string;
  is_mandatory: boolean;
  applicability: string;
}

export interface Bidder {
  id: string;
  legal_name: string;
  trade_name?: string;
  pan?: string;
  gstin?: string;
  udyam_registration_number?: string;
  is_mse: boolean;
  is_startup: boolean;
  compliance_score?: number;
  risk_level?: FindingSeverity;
}

export interface ComplianceMatrixItem {
  id: string;
  dimension: string;
  requirement_description: string;
  required_value: string;
  bidder_extracted_value: string;
  status: MatrixItemStatus;
  is_statutory: boolean;
  confidence_score: number;
  citations: Array<{
    source_type: 'TENDER' | 'BIDDER_DOCUMENT';
    page_number: number;
    snippet: string;
  }>;
  notes?: string;
}

export interface OfficerFinding {
  id: string;
  application_id?: string;
  applicationId?: string;
  bidder_name?: string;
  matrix_item_id?: string;
  title: string;
  description: string;
  severity: FindingSeverity;
  finding_type: string;
  recommended_action: string;
  review_status: FindingReviewStatus;
  officer_notes?: string;
  overridden_at?: string;
}

export interface VerificationRecord {
  id: string;
  source_type: 'GST' | 'UDYAM_MSME' | 'PAN' | 'DEBARMENT';
  identifier_value: string;
  status: VerificationStatus;
  name_match_score: number;
  verified_entity_name: string;
  verification_date: string;
  details: Record<string, any>;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity_type: string;
  details: string;
}

export type DetailedVerificationResult =
  | 'COMPLIANT'
  | 'NON_COMPLIANT'
  | 'PARTIAL'
  | 'NOT_VERIFIABLE'
  | 'EVIDENCE_MISSING'
  | 'CLARIFICATION_PENDING'
  | 'NOT_EVALUATED';

export interface BidderApplicationDocument {
  id: string;
  file_name: string;
  title: string;
  document_type: string;
  pages: number;
  processing_status: 'PROCESSED' | 'EXTRACTED' | 'INDEXED' | 'PENDING';
  extraction_status: 'COMPLETE' | 'PARTIAL' | 'FAILED';
  verification_status: DetailedVerificationResult;
  evidence_availability: 'AVAILABLE' | 'PARTIAL' | 'OMITTED';
  description: string;
  key_clauses: string[];
  extracted_items?: Array<{
    label: string;
    value: string;
    page: number;
    cross_reference?: string;
    discrepancy_note?: string;
  }>;
  content_preview?: string;
}

export interface BidderApplicationPackage {
  id: string;
  bidder_name: string;
  trade_name: string;
  is_synthetic: boolean;
  tender_id: string;
  submission_date: string;
  cin: string;
  pan: string;
  gstin: string;
  udyam_number: string;
  registered_address: string;
  authorized_signatory: string;
  total_documents: number;
  total_pages: number;
  requirements_mapped: number;
  verified_count: number;
  issues_count: number;
  overall_status: 'REVIEW_REQUIRED' | 'PARTIAL' | 'FLAGGED' | 'COMPLIANT';
  documents: BidderApplicationDocument[];
}

export interface DocumentVerificationCheck {
  id: string;
  category: 'Identity' | 'Financial' | 'Experience' | 'Statutory' | 'Authorization' | 'EMD' | 'Technical' | 'Declarations';
  requirement_title: string;
  requirement_clause: string;
  requirement_text: string;
  submitted_evidence: string;
  extraction_details: string;
  cross_document_evidence?: string;
  variance?: string;
  verification_method: string;
  result: DetailedVerificationResult;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  source_document: string;
  source_page: number;
  finding_id?: string;
  finding_title?: string;
}

export interface AIStatusInfo {
  status: 'connected' | 'fallback_active' | 'unavailable' | 'auth_required';
  provider: string;
  model: string;
  device: string;
  connection_status: string;
  last_request_time?: string;
  fallback_status: string;
  auth_error?: boolean;
}

