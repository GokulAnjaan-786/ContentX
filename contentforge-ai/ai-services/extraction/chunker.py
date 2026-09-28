import math
from typing import Any, Dict, List, Optional, Union
from app.core.config import settings
from ai_services.retrieval.content_filter import classify_content_text


def chunk_document(
    content: Union[str, List[Dict[str, Any]]],
    target_words: int = 600,
    overlap_words: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split document content into ~500-800 word chunks with ~50-word overlap,
    preserving page number and section/paragraph references.

    Args:
        content: Either raw string text or list of structured items
                 [{"text": str, "page_number": int, "section": str}, ...]
        target_words: Target word size per chunk (default 600)
        overlap_words: Number of overlapping words between consecutive chunks (default 50)

    Returns:
        List of dicts:
        [
            {
                "chunk_index": int,
                "text": str,
                "word_count": int,
                "page_number": Optional[int],
                "section_reference": Optional[str],
            },
            ...
        ]
    """
    # Normalize input into list of token tuples: (word, page_number, section)
    tokens = []

    if isinstance(content, str):
        items = [{"text": content, "page_number": 1, "section": "Body"}]
    else:
        items = content

    for item in items:
        text = item.get("text", "")
        if not text:
            continue
        page_num = item.get("page_number")
        section = item.get("section") or item.get("section_reference")

        words = text.split()
        for w in words:
            tokens.append((w, page_num, section))

    if not tokens:
        return []

    total_words = len(tokens)
    step = max(1, target_words - overlap_words)
    chunks = []
    chunk_index = 0
    start = 0

    while start < total_words:
        end = min(start + target_words, total_words)

        # If remaining tail is small (< 100 words), merge into the current chunk
        if total_words - end < 100:
            end = total_words

        window = tokens[start:end]
        chunk_words = [t[0] for t in window]
        chunk_text = " ".join(chunk_words)

        # Identify starting or predominant page and section
        page_numbers = [t[1] for t in window if t[1] is not None]
        sections = [t[2] for t in window if t[2] is not None]

        page_ref = page_numbers[0] if page_numbers else None
        section_ref = sections[0] if sections else None

        chunks.append({
            "chunk_index": chunk_index,
            "text": chunk_text,
            "word_count": len(chunk_words),
            "page_number": page_ref,
            "section_reference": str(section_ref) if section_ref else None,
            "content_type": classify_content_text(chunk_text),
        })

        chunk_index += 1
        if end >= total_words:
            break
        start += step

    return chunks

