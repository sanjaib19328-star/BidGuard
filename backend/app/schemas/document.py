import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentProcessingStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    organization_id: uuid.UUID
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    processing_status: DocumentProcessingStatus
    uploaded_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
