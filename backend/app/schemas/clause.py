import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClauseCategory


class ClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    document_id: uuid.UUID
    page_id: Optional[uuid.UUID] = None
    page_number: int
    clause_number: Optional[str] = None
    title: Optional[str] = None
    clause_text: str
    category: ClauseCategory
    sequence_order: int
    extraction_method: str
    confidence: float
    created_at: datetime
    updated_at: datetime


class ClauseListResponse(BaseModel):
    items: List[ClauseResponse]
    total: int
    page: int
    page_size: int
    tender_id: uuid.UUID
    categories_breakdown: Dict[str, int]


class ClauseExtractionRequest(BaseModel):
    force_reextract: bool = Field(
        default=False,
        description="Whether to overwrite and re-extract existing clauses for this tender",
    )


class ClauseExtractionResponse(BaseModel):
    tender_id: uuid.UUID
    total_clauses: int
    categories_breakdown: Dict[str, int]
    message: str
