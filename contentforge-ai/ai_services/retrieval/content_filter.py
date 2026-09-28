import re
from typing import Any, Dict, List, Tuple
from ai_services.retrieval.query_intent import QueryIntent

METADATA_COPYRIGHT_KEYWORDS = [
    "copyright", "all rights reserved", "cashflow technologies", "plata publishing",
    "isbn", "printed in", "stolen property", "disclaim any liability", "legal or other expert assistance",
    "published by", "publication date", "cataloging-in-publication", "trademarks",
    "author:", "publisher:", "rights reserved", "first printing", "edition:"
]

TOC_KEYWORDS = [
    "contents", "table of contents", "chapter one", "chapter two", "chapter three",
    "chapter 1", "chapter 2", "chapter 3", "acknowledgments", "dedication", "preface"
]

BODY_CONTENT_KEYWORDS = [
    "rich dad", "poor dad", "financial education", "asset", "liability", "income statement",
    "balance sheet", "cash flow", "money", "investing", "wealth", "lesson", "principle",
    "quadrant", "vulnerability", "finding", "mitigation", "analysis", "result", "strategy"
]


def classify_content_text(text: str) -> str:
    """
    Classify text into a structural content role:
    - copyright: Copyright notices, publisher legal disclaimers, ISBN, trademark warnings
    - metadata: Author, publisher, title page info, document publication attributes
    - table_of_contents: Chapter indexes, navigation lists
    - conclusion: Summary findings, final takeaways
    - introduction: Preamble, forward, book overview
    - chapter / section / body: Core substantive document text
    """
    if not text or not text.strip():
        return "noise"

    text_lower = text.lower().strip()

    # 1. Check for Copyright / Legal disclaimers
    copyright_matches = sum(1 for k in METADATA_COPYRIGHT_KEYWORDS if k in text_lower)
    if copyright_matches >= 2 or any(k in text_lower for k in ["copyright ©", "stolen property", "plata publishing", "cashflow technologies"]):
        return "copyright"

    # 2. Check for Table of Contents / Indexing
    if any(k in text_lower for k in ["table of contents", "contents..."]) or re.search(r"chapter\s+\w+\.\.\.\.\.\.\.\.\.\.\.\.\.", text_lower):
        return "table_of_contents"

    # 3. Check for Document Metadata
    if any(k in text_lower for k in ["isbn-13:", "isbn-10:", "printed in the united states", "all rights reserved"]):
        return "metadata"

    # 4. Check for Conclusion / Summary
    if any(k in text_lower for k in ["in summary", "conclusion", "final thoughts", "in closing", "summary of key lessons"]):
        return "conclusion"

    # 5. Check for Chapter / Section headers
    if re.search(r"\bchapter\s+\d+\b", text_lower) or re.search(r"\bsection\s+\d+\b", text_lower):
        return "chapter"

    # Default: Body content
    return "body"


def calculate_content_role_score(content_type: str, query_intent: QueryIntent) -> float:
    """
    Return a content role weight between 0.0 and 1.0 based on query intent.
    For CONTENT_GENERATION queries, copyright and metadata are scored 0.0 - 0.1,
    while core body/chapter content is scored 0.9 - 1.0.
    """
    if query_intent.allow_metadata:
        # User explicitly asked for metadata
        role_weights = {
            "metadata": 1.0,
            "copyright": 0.8,
            "introduction": 0.9,
            "chapter": 0.7,
            "body": 0.6,
            "conclusion": 0.6,
            "table_of_contents": 0.4,
            "noise": 0.0,
        }
    else:
        # Standard content generation request: Prioritize body and chapter content
        role_weights = {
            "body": 1.0,
            "chapter": 0.95,
            "section": 0.90,
            "conclusion": 0.85,
            "introduction": 0.60,
            "table_of_contents": 0.20,
            "metadata": 0.10,
            "copyright": 0.0,
            "noise": 0.0,
        }

    return role_weights.get(content_type, 0.5)


def filter_candidate_chunks(
    chunks: List[Any],
    query_intent: QueryIntent,
    max_candidates: int = 20,
) -> List[Tuple[Any, str, float]]:
    """
    Classify and filter candidate chunks, returning tuples of (chunk, content_type, role_score).
    Removes zero-weight copyright/noise chunks for content-generation requests.
    """
    classified_chunks = []

    for c in chunks:
        text = c.text if hasattr(c, "text") else str(c)
        content_type = getattr(c, "content_type", None) or classify_content_text(text)
        role_score = calculate_content_role_score(content_type, query_intent)

        # Filter out zero-score chunks unless metadata is explicitly allowed
        if role_score <= 0.05 and not query_intent.allow_metadata:
            continue

        classified_chunks.append((c, content_type, role_score))

    # If filtering removed all chunks, fallback to top candidate chunks
    if not classified_chunks and chunks:
        for c in chunks[:5]:
            text = c.text if hasattr(c, "text") else str(c)
            ct = classify_content_text(text)
            classified_chunks.append((c, ct, 0.5))

    return classified_chunks[:max_candidates]
