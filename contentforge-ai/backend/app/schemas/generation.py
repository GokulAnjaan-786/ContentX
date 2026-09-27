import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FactRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    fact_id_string: str
    fact_statement: str
    source_chunk_id: Optional[uuid.UUID] = None
    source_snippet: Optional[str] = None
    confidence: float
    created_at: datetime


class FactRegistryListResponse(BaseModel):
    document_id: uuid.UUID
    total_facts: int
    facts: List[FactRegistryOut]


class ContentMetadataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    summary: str
    document_type: str
    entities: Dict[str, Any]
    topics: List[str]
    created_at: datetime


class GenerationRequest(BaseModel):
    document_id: uuid.UUID
    selected_outputs: List[str] = Field(
        ...,
        description="List of outputs to generate: linkedin, twitter, advisory, executive_summary, presentation, infographic, video_package",
        json_schema_extra={"example": ["linkedin", "twitter", "advisory", "executive_summary"]},
    )
    selected_audiences: Optional[List[str]] = Field(
        default_factory=lambda: ["automatic"],
        description="List of target audience levels: technical, executive, professional, general_public, automatic",
    )
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "audience": "executive",
            "tone": "authoritative",
            "language": "en",
            "detail_level": "standard",
            "objective": "briefing",
        }
    )


class GenerationJobResponse(BaseModel):
    job_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    selected_outputs: List[str]
    message: str = "Generation job queued successfully"


class GeneratedOutputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    output_type: str
    content: Dict[str, Any]
    validation_score: float
    status: str
    fact_ids_used: List[str]
    unverified_claims: List[Any]
    created_at: datetime


class GenerationJobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    error_message: Optional[str] = None
    selected_outputs: List[str]
    settings: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None


class GenerationOutputsListResponse(BaseModel):
    job_id: uuid.UUID
    total_outputs: int
    outputs: List[GeneratedOutputOut]


class OutputUpdateRequest(BaseModel):
    content: Dict[str, Any]


class HistoryItemOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    status: str
    selected_outputs: List[str]
    created_at: datetime

