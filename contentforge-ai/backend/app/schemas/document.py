import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.document import ProcessedStatus, SourceType


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    status: ProcessedStatus
    message: str = "Document uploaded successfully and queued for processing"


class DocumentChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    section_reference: Optional[str] = None
    word_count: Optional[int] = None
    created_at: datetime


class DocumentChunksListResponse(BaseModel):
    document_id: uuid.UUID
    total_chunks: int
    chunks: List[DocumentChunkOut]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    uploaded_by: Optional[uuid.UUID] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    source_type: SourceType
    sensitivity_flag: str
    processed_status: ProcessedStatus
    error_message: Optional[str] = None
    pii_detected: bool = False
    pii_types: List[str] = Field(default_factory=list)
    injection_flagged: bool = False
    injection_details: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
