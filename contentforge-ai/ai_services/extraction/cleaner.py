import re
from collections import Counter
from typing import Any, Dict, List


def remove_repeated_headers_footers(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect and strip recurring running headers and footers across pages.
    """
    if len(pages) < 2:
        return pages

    top_lines = []
    bottom_lines = []

    # Collect header and footer candidate lines
    for page in pages:
        lines = [line.strip() for line in page["text"].split("\n") if line.strip()]
        if lines:
            top_lines.append(lines[0])
            if len(lines) > 1:
                bottom_lines.append(lines[-1])

    threshold = max(2, int(len(pages) * 0.45))
    repeated_headers = {line for line, count in Counter(top_lines).items() if count >= threshold}
    repeated_footers = {line for line, count in Counter(bottom_lines).items() if count >= threshold}

    # Common standalone page-number patterns (e.g., "1", "Page 1 of 10", "- 1 -")
    page_num_pattern = re.compile(
        r"^(page\s+\d+(\s+of\s+\d+)?|-?\s*\d+\s*-?|confidential)$", re.IGNORECASE
    )

    cleaned_pages = []
    for page in pages:
        lines = [line.strip() for line in page["text"].split("\n")]
        # Filter top lines if header
        while lines and lines[0] in repeated_headers:
            lines.pop(0)

        # Filter bottom lines if footer or standalone page number
        while lines and (lines[-1] in repeated_footers or page_num_pattern.match(lines[-1])):
            lines.pop()

        cleaned_pages.append({
            **page,
            "text": "\n".join(lines),
        })

    return cleaned_pages


def fix_broken_line_breaks(text: str) -> str:
    """
    Fix hyphenated words split across newlines and join broken sentence lines
    while preserving actual paragraph breaks.
    """
    # 1. Rejoin words split with a trailing hyphen (e.g. "transfor-\nmation" -> "transformation")
    text = re.sub(r"(\b[a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,}\b)", r"\1\2", text)

    # 2. Join lines inside a paragraph that were broken by artificial wrapping
    lines = text.split("\n")
    reconstructed: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if reconstructed and reconstructed[-1] != "":
                reconstructed.append("")
            continue

        if reconstructed and reconstructed[-1] != "":
            prev = reconstructed[-1]
            # If the previous line did not end with sentence-ending punctuation or colon/bullet
            if not re.search(r'[.!?:\u2022\u2023\u25E6\-\*]$', prev) and not re.match(r'^[\u2022\u2023\u25E6\-\*\d+\.]', stripped):
                reconstructed[-1] = f"{prev} {stripped}"
            else:
                reconstructed.append(stripped)
        else:
            reconstructed.append(stripped)

    return "\n\n".join([p for p in reconstructed if p])


def normalize_whitespace(text: str) -> str:
    """
    Normalise irregular spaces, tabs, carriage returns, and excessive newlines.
    """
    # Replace non-breaking spaces and unicode spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace multiple horizontal spaces/tabs with single space
    text = re.sub(r"[^\S\n]+", " ", text)

    # Limit consecutive newlines to at most two (paragraph separation)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_text(text: str) -> str:
    """Run full cleaning pipeline on a raw text string."""
    text = fix_broken_line_breaks(text)
    text = normalize_whitespace(text)
    return text


def clean_extracted_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean a collection of extracted pages (with headers/footers removed)."""
    pages_without_headers = remove_repeated_headers_footers(pages)
    cleaned = []
    for p in pages_without_headers:
        cleaned_text = clean_text(p["text"])
        if cleaned_text:
            cleaned.append({
                **p,
                "text": cleaned_text,
            })
    return cleaned
