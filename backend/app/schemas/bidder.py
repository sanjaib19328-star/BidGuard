import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import (
    BidderDocumentType,
    DocumentProcessingStatus,
    EntityType,
    MseCategory,
    ParticipationStatus,
)


class BidderCreateRequest(BaseModel):
    legal_name: str = Field(..., min_length=2, max_length=255, description="Registered legal entity name")
    trade_name: Optional[str] = Field(None, max_length=255, description="Trade name or DBA if applicable")
    gstin: Optional[str] = Field(None, min_length=15, max_length=15, description="15-character GSTIN")
    pan: Optional[str] = Field(None, min_length=10, max_length=10, description="10-character PAN")
    udyam_registration_number: Optional[str] = Field(None, max_length=50, description="Udyam registration number")
    registered_address: Optional[str] = Field(None, description="Registered business address")
    contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Primary contact phone")
    primary_contact_person: Optional[str] = Field(None, max_length=255, description="Name of contact officer")
    is_mse: bool = Field(False, description="Whether bidder claims Micro or Small Enterprise status")
    mse_category: MseCategory = Field(MseCategory.NOT_APPLICABLE, description="Micro, Small, or Medium")
    asme_stamp_holder: bool = Field(False, description="Whether bidder holds ASME U/U2 Code Stamp")
    asme_certificate_number: Optional[str] = Field(None, max_length=100, description="ASME authorization number")


class BidderUpdateRequest(BaseModel):
    legal_name: Optional[str] = Field(None, min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    gstin: Optional[str] = Field(None, min_length=15, max_length=15)
    pan: Optional[str] = Field(None, min_length=10, max_length=10)
    udyam_registration_number: Optional[str] = Field(None, max_length=50)
    registered_address: Optional[str] = Field(None)
    contact_email: Optional[EmailStr] = Field(None)
    contact_phone: Optional[str] = Field(None, max_length=50)
    primary_contact_person: Optional[str] = Field(None, max_length=255)
    is_mse: Optional[bool] = Field(None)
    mse_category: Optional[MseCategory] = Field(None)
    asme_stamp_holder: Optional[bool] = Field(None)
    asme_certificate_number: Optional[str] = Field(None, max_length=100)


class BidderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    legal_name: str
    trade_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    udyam_registration_number: Optional[str] = None
    registered_address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    primary_contact_person: Optional[str] = None
    is_mse: bool
    mse_category: MseCategory
    asme_stamp_holder: bool
    asme_certificate_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BidderListResponse(BaseModel):
    bidders: List[BidderResponse]
    total: int
    page: int
    page_size: int


class BidderDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bidder_id: uuid.UUID
    tender_id: Optional[uuid.UUID] = None
    document_type: BidderDocumentType
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    processing_status: DocumentProcessingStatus
    page_count: int
    created_at: datetime
    updated_at: datetime


class BidderDocumentListResponse(BaseModel):
    documents: List[BidderDocumentResponse]
    total: int


class ExtractedEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bidder_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    page_number: Optional[int] = None
    entity_type: EntityType
    raw_value: str
    normalized_value: str
    confidence: float
    context_snippet: Optional[str] = None
    bounding_box: Optional[Dict[str, Any]] = None
    created_at: datetime


class ExtractedEntityListResponse(BaseModel):
    entities: List[ExtractedEntityResponse]
    total: int


class BidderTenderParticipationCreateRequest(BaseModel):
    tender_id: uuid.UUID
    status: ParticipationStatus = ParticipationStatus.SUBMITTED
    submission_date: Optional[datetime] = None
    officer_notes: Optional[str] = None


class BidderTenderParticipationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bidder_id: uuid.UUID
    tender_id: uuid.UUID
    status: ParticipationStatus
    submission_date: Optional[datetime] = None
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    officer_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentExtractRunResponse(BaseModel):
    document_id: uuid.UUID
    classified_type: BidderDocumentType
    confidence: float
    pages_processed: int
    extracted_entities_count: int
    entities: List[ExtractedEntityResponse]


class BidderProfileSummaryResponse(BaseModel):
    bidder: BidderResponse
    documents_count: int
    participations_count: int
    extracted_entities_count: int
    participations: List[BidderTenderParticipationResponse]
