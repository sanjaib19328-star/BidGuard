import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models.enums import TenderStatus


class TenderCreateRequest(BaseModel):
    tender_number: str = Field(..., min_length=1, max_length=100, description="Unique tender identifier / number")
    title: str = Field(..., min_length=1, max_length=255, description="Title of the tender")
    description: Optional[str] = Field(default=None, description="Detailed description of the tender requirements")
    procuring_entity: Optional[str] = Field(default=None, max_length=255, description="Procuring agency or department name")
    department: Optional[str] = Field(default=None, max_length=255, description="Department name")
    category: Optional[str] = Field(default=None, max_length=100, description="Tender category (Goods, Works, Services)")
    tender_type: Optional[str] = Field(default=None, max_length=100, description="Type of tender (Open, Limited, EOI)")
    source_portal: Optional[str] = Field(default="GeM", max_length=100, description="Source procurement portal (e.g. GeM, CPPP)")
    source_url: Optional[HttpUrl] = Field(default=None, description="Source portal URL link")
    issue_date: Optional[datetime] = Field(default=None, description="Tender issuance date")
    submission_deadline: datetime = Field(..., description="Mandatory bid submission deadline")
    opening_date: Optional[datetime] = Field(default=None, description="Technical / Commercial bid opening date")

    @field_validator("title", "tender_number")
    @classmethod
    def not_empty_after_strip(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped


class TenderUpdateRequest(BaseModel):
    tender_number: Optional[str] = Field(default=None, min_length=1, max_length=100)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    procuring_entity: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    tender_type: Optional[str] = Field(default=None, max_length=100)
    source_portal: Optional[str] = Field(default=None, max_length=100)
    source_url: Optional[HttpUrl] = None
    issue_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    opening_date: Optional[datetime] = None

    @field_validator("title", "tender_number")
    @classmethod
    def not_empty_if_provided(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return stripped
        return v


class TenderStatusUpdateRequest(BaseModel):
    status: TenderStatus = Field(..., description="Target lifecycle status")


class TenderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    tender_number: str
    title: str
    description: Optional[str] = None
    procuring_entity: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None
    tender_type: Optional[str] = None
    source_portal: Optional[str] = None
    source_url: Optional[str] = None
    issue_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    opening_date: Optional[datetime] = None
    status: TenderStatus
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class TenderListResponse(BaseModel):
    items: List[TenderResponse]
    total: int
    page: int
    page_size: int
