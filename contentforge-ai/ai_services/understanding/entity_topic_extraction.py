from typing import List, Optional
from pydantic import BaseModel, Field


class EntitiesSchema(BaseModel):
    people: List[str] = Field(default_factory=list)
    organisations: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    products_systems: List[str] = Field(default_factory=list)


class FactExtractionItem(BaseModel):
    statement: str = Field(..., description="Atomic, standalone factual statement")
    source_chunk_index: Optional[int] = Field(None, description="0-indexed chunk number where fact was found")
    source_snippet: Optional[str] = Field(None, description="Exact or near-exact sentence from source document")
    fact_type: Optional[str] = Field("incident_finding", description="incident_finding, technical_detail, action_item, risk_recommendation, statistic, document_metadata, internal_processing")
    importance: Optional[str] = Field("high", description="high, medium, low, metadata, internal")
    certainty_status: Optional[str] = Field("confirmed", description="confirmed, uncertain, unsupported")
    entities: List[str] = Field(default_factory=list, description="Entities mentioned in this fact")
    dates: List[str] = Field(default_factory=list, description="Dates or times mentioned in this fact")
    numbers: List[str] = Field(default_factory=list, description="Key metrics or numbers mentioned in this fact")


class UnderstandingPassSchema(BaseModel):
    summary: str = Field(..., description="3-5 line comprehensive document summary")
    document_type: str = Field(
        ...,
        description="Type: incident_report, research_paper, policy, advisory, article, or other",
    )
    entities: EntitiesSchema = Field(default_factory=EntitiesSchema)
    topics: List[str] = Field(default_factory=list)
    key_facts: List[FactExtractionItem] = Field(default_factory=list)

