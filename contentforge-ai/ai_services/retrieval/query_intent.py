import re
from enum import Enum
from typing import Dict, List, Set


class QueryIntentType(str, Enum):
    CONTENT_GENERATION = "CONTENT_GENERATION"
    SUMMARY = "SUMMARY"
    KEY_INSIGHTS = "KEY_INSIGHTS"
    FACTUAL_LOOKUP = "FACTUAL_LOOKUP"
    METADATA_LOOKUP = "METADATA_LOOKUP"
    AUTHOR_LOOKUP = "AUTHOR_LOOKUP"
    DATE_LOOKUP = "DATE_LOOKUP"
    GENERAL_QUESTION = "GENERAL_QUESTION"


class QueryIntent:
    def __init__(
        self,
        intent_type: QueryIntentType,
        target_format: str,
        allow_metadata: bool = False,
        preferred_content_types: List[str] = None,
        deprioritized_content_types: List[str] = None,
    ):
        self.intent_type = intent_type
        self.target_format = target_format
        self.allow_metadata = allow_metadata
        self.preferred_content_types = preferred_content_types or ["body", "chapter", "section", "conclusion"]
        self.deprioritized_content_types = deprioritized_content_types or ["metadata", "copyright", "publisher", "isbn", "table_of_contents"]

    def to_dict(self) -> Dict:
        return {
            "intent_type": self.intent_type.value,
            "target_format": self.target_format,
            "allow_metadata": self.allow_metadata,
            "preferred_content_types": self.preferred_content_types,
            "deprioritized_content_types": self.deprioritized_content_types,
        }


def detect_query_intent(query: str, target_format: str = "general") -> QueryIntent:
    """
    Classify query into intent type and determine whether document metadata
    or substantive content should be prioritized.
    """
    query_lower = query.lower().strip()

    # 1. Author Lookup
    if any(k in query_lower for k in ["who wrote", "who is the author", "author of", "written by"]):
        return QueryIntent(
            intent_type=QueryIntentType.AUTHOR_LOOKUP,
            target_format=target_format,
            allow_metadata=True,
            preferred_content_types=["metadata", "introduction", "body"],
            deprioritized_content_types=[],
        )

    # 2. Date / Publication Lookup
    if any(k in query_lower for k in ["when was", "publication date", "published in", "year of publication", "what year"]):
        return QueryIntent(
            intent_type=QueryIntentType.DATE_LOOKUP,
            target_format=target_format,
            allow_metadata=True,
            preferred_content_types=["metadata", "introduction", "body"],
            deprioritized_content_types=[],
        )

    # 3. Explicit Metadata Lookup
    if any(k in query_lower for k in ["publisher", "isbn", "copyright", "edition", "document metadata", "file details"]):
        return QueryIntent(
            intent_type=QueryIntentType.METADATA_LOOKUP,
            target_format=target_format,
            allow_metadata=True,
            preferred_content_types=["metadata", "copyright", "introduction"],
            deprioritized_content_types=[],
        )

    # 4. Content Generation (LinkedIn, Twitter, Advisory, Video, Presentation, Infographic)
    if target_format in ("linkedin", "twitter", "advisory", "presentation", "infographic", "video_package") or any(
        k in query_lower for k in ["create", "generate", "write a", "linkedin", "tweet", "post", "slide", "script", "article"]
    ):
        return QueryIntent(
            intent_type=QueryIntentType.CONTENT_GENERATION,
            target_format=target_format,
            allow_metadata=False,
            preferred_content_types=["body", "chapter", "section", "conclusion", "introduction"],
            deprioritized_content_types=["metadata", "copyright", "publisher", "isbn", "table_of_contents", "reference"],
        )

    # 5. Summary Request
    if any(k in query_lower for k in ["summarize", "summary", "overview", "briefing"]):
        return QueryIntent(
            intent_type=QueryIntentType.SUMMARY,
            target_format=target_format,
            allow_metadata=False,
            preferred_content_types=["body", "chapter", "section", "conclusion"],
            deprioritized_content_types=["metadata", "copyright", "publisher", "isbn", "table_of_contents"],
        )

    # 6. Key Insights / Lessons
    if any(k in query_lower for k in ["lesson", "insight", "takeaway", "principle", "rule", "finding", "asset", "liability"]):
        return QueryIntent(
            intent_type=QueryIntentType.KEY_INSIGHTS,
            target_format=target_format,
            allow_metadata=False,
            preferred_content_types=["body", "chapter", "section", "conclusion"],
            deprioritized_content_types=["metadata", "copyright", "publisher", "isbn", "table_of_contents"],
        )

    # 7. Factual Lookup
    if any(k in query_lower for k in ["what is", "how does", "why did", "explain", "describe", "definition"]):
        return QueryIntent(
            intent_type=QueryIntentType.FACTUAL_LOOKUP,
            target_format=target_format,
            allow_metadata=False,
            preferred_content_types=["body", "chapter", "section"],
            deprioritized_content_types=["metadata", "copyright", "table_of_contents"],
        )

    # Default: General Question
    return QueryIntent(
        intent_type=QueryIntentType.GENERAL_QUESTION,
        target_format=target_format,
        allow_metadata=False,
        preferred_content_types=["body", "chapter", "section", "conclusion"],
        deprioritized_content_types=["metadata", "copyright", "table_of_contents"],
    )
