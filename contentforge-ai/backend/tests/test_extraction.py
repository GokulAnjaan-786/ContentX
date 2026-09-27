import pytest
from ai_services.extraction.chunker import chunk_document
from ai_services.extraction.cleaner import (
    clean_text,
    fix_broken_line_breaks,
    normalize_whitespace,
    remove_repeated_headers_footers,
)
from ai_services.extraction.pdf_extractor import extract_text_from_pdf
from ai_services.extraction.docx_extractor import extract_text_from_docx


def test_chunking_known_word_count_and_overlap():
    """
    Given a known input of 1150 words, with target_words=600 and overlap_words=50:
    - Chunk 1: words 0 to 600 (600 words)
    - Next chunk start: 600 - 50 = 550
    - Chunk 2: words 550 to 1150 (600 words)
    - Total chunks = 2, with exactly 50 words shared between them.
    """
    words = [f"word{i}" for i in range(1150)]
    sample_text = " ".join(words)

    chunks = chunk_document(sample_text, target_words=600, overlap_words=50)

    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"

    chunk1_words = chunks[0]["text"].split()
    chunk2_words = chunks[1]["text"].split()

    assert len(chunk1_words) == 600
    assert len(chunk2_words) == 600

    # Test overlap: the last 50 words of chunk 1 must match the first 50 words of chunk 2
    overlap_chunk1 = chunk1_words[-50:]
    overlap_chunk2 = chunk2_words[:50]
    assert overlap_chunk1 == overlap_chunk2, "Chunk overlap does not match!"
    assert overlap_chunk1 == [f"word{i}" for i in range(550, 600)]


def test_chunking_small_input():
    """Inputs smaller than target_words produce a single chunk."""
    text = "Short advisory document with only eight words."
    chunks = chunk_document(text, target_words=600, overlap_words=50)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["word_count"] == 7
    assert chunks[0]["text"] == text


def test_chunking_preserves_page_references():
    """Structured input retains page and section provenance in chunks."""
    pages = [
        {"page_number": 1, "section": "Introduction", "text": "Page one intro with distinct facts."},
        {"page_number": 2, "section": "Analysis", "text": "Page two analysis with additional details."},
    ]
    chunks = chunk_document(pages, target_words=600, overlap_words=50)
    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["section_reference"] == "Introduction"


def test_cleaner_repeated_headers_and_footers():
    """Repeated headers and footers across pages are identified and removed."""
    pages = [
        {
            "page_number": 1,
            "text": "ACME GLOBAL CONFIDENTIAL REPORT\nPage 1 content here.\nPage 1 of 3",
        },
        {
            "page_number": 2,
            "text": "ACME GLOBAL CONFIDENTIAL REPORT\nPage 2 content here.\nPage 2 of 3",
        },
        {
            "page_number": 3,
            "text": "ACME GLOBAL CONFIDENTIAL REPORT\nPage 3 content here.\nPage 3 of 3",
        },
    ]

    cleaned_pages = remove_repeated_headers_footers(pages)
    for p in cleaned_pages:
        assert "ACME GLOBAL CONFIDENTIAL REPORT" not in p["text"]
        assert "Page 1 of 3" not in p["text"]
        assert "Page 2 of 3" not in p["text"]
        assert "Page 3 of 3" not in p["text"]
        assert "content here." in p["text"]


def test_cleaner_hyphenated_line_breaks():
    """Hyphenated words split across lines are reunited."""
    raw = "The model handles automated transfor-\nmation and orches-\ntration smoothly."
    cleaned = fix_broken_line_breaks(raw)
    assert "transformation" in cleaned
    assert "orchestration" in cleaned
    assert "transfor-" not in cleaned


def test_cleaner_whitespace_and_newlines():
    """Excessive newlines and irregular spaces are normalized."""
    raw = "Line 1   with   extra    spaces.\n\n\n\nLine 2.\u00a0Non-breaking space."
    cleaned = normalize_whitespace(raw)
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "\u00a0" not in cleaned


def test_pdf_extractor(sample_pdf_bytes):
    """PyMuPDF successfully extracts text per page."""
    pages = extract_text_from_pdf(sample_pdf_bytes)
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "ContentForge AI Executive Briefing" in pages[0]["text"]
    assert pages[1]["page_number"] == 2
    assert "Performance and Verification" in pages[1]["text"]


def test_docx_extractor(sample_docx_bytes):
    """python-docx successfully extracts paragraphs and headings."""
    elements = extract_text_from_docx(sample_docx_bytes)
    assert len(elements) >= 3
    texts = [e["text"] for e in elements]
    assert any("ContentForge AI Advisory Report" in t for t in texts)
    assert any("All facts are anchored" in t for t in texts)
