import logging
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)


# 1. LinkedIn Schema
class LinkedInOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hook: str = Field(..., description="Opening single-line hook")
    body: str = Field(..., description="Post body under 200 words")
    hashtags: List[str] = Field(default_factory=list)
    call_to_action: str = Field(..., description="Closing call to action")
    fact_ids_used: List[str] = Field(default_factory=list)


# 2. Twitter / X Schema
class TweetItem(BaseModel):
    order: int
    text: str = Field(..., max_length=280)


class TwitterOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tweets: List[TweetItem] = Field(..., min_length=1, max_length=10)
    fact_ids_used: List[str] = Field(default_factory=list)


# 3. Advisory Schema
class AdvisoryOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    severity: str
    summary: str
    scope: str
    details: str
    recommended_actions: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    fact_ids_used: List[str] = Field(default_factory=list)


# 4. Executive Summary Schema
class ExecutiveSummaryOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    summary_text: str
    key_takeaways: List[str] = Field(default_factory=list)
    fact_ids_used: List[str] = Field(default_factory=list)


# 5. Infographic Schema
class InfographicSection(BaseModel):
    order: int
    stat_or_point: str
    icon_suggestion: str


class InfographicOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    headline: str
    sections: List[InfographicSection] = Field(default_factory=list)
    layout_style: str
    colour_theme: str
    fact_ids_used: List[str] = Field(default_factory=list)


# 6. Presentation Schema
class SlideItem(BaseModel):
    slide_no: int
    title: str
    bullets: List[str] = Field(default_factory=list)
    speaker_notes: str
    visual_suggestion: str


class PresentationOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requested_slide_count: int = Field(default=5)
    actual_slide_count: int = Field(default=5)
    title: str = Field(default="Strategic Presentation Overview")
    slides: List[SlideItem] = Field(default_factory=list)
    fact_ids_used: List[str] = Field(default_factory=list)


# 7. Video Package Schema
class SceneItem(BaseModel):
    scene_no: int
    narration: str
    visual_description: str
    subtitle_text: str
    duration_estimate_sec: int


class VideoPackageOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    total_duration_estimate: str
    scenes: List[SceneItem] = Field(default_factory=list)
    fact_ids_used: List[str] = Field(default_factory=list)


OUTPUT_SCHEMA_MAP: Dict[str, Type[BaseModel]] = {
    "linkedin": LinkedInOutput,
    "twitter": TwitterOutput,
    "advisory": AdvisoryOutput,
    "executive_summary": ExecutiveSummaryOutput,
    "infographic": InfographicOutput,
    "presentation": PresentationOutput,
    "video_package": VideoPackageOutput,
}


def get_schema_for_type(output_type: str) -> Optional[Type[BaseModel]]:
    """Return Pydantic schema class for a given output format identifier."""
    return OUTPUT_SCHEMA_MAP.get(output_type.lower())


def validate_output_schema(output_type: str, data: Dict[str, Any]) -> Tuple[bool, Optional[BaseModel], Optional[str]]:
    """
    Validate generator dictionary output against its corresponding schema.
    Returns: (is_valid, validated_model, error_message)
    """
    schema_cls = get_schema_for_type(output_type)
    if not schema_cls:
        return False, None, f"Unknown output type: '{output_type}'"

    try:
        validated = schema_cls.model_validate(data)
        return True, validated, None
    except ValidationError as ve:
        err_msg = str(ve)
        logger.warning(f"Schema validation failed for {output_type}: {err_msg}")
        return False, None, err_msg
