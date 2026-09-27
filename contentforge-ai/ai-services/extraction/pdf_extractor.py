import io
import logging
from typing import Any, Dict, List, Union
import pymupdf

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_input: Union[bytes, str, io.BytesIO]) -> List[Dict[str, Any]]:
    """
    Extract text page-by-page from a PDF document using PyMuPDF.

    Args:
        file_input: Raw PDF bytes, file path string, or BytesIO buffer.

    Returns:
        List of dicts: [{"page_number": int, "text": str}]
    """
    pages: List[Dict[str, Any]] = []

    try:
        if isinstance(file_input, bytes):
            doc = pymupdf.open(stream=file_input, filetype="pdf")
        elif isinstance(file_input, io.BytesIO):
            doc = pymupdf.open(stream=file_input.getvalue(), filetype="pdf")
        elif isinstance(file_input, str):
            doc = pymupdf.open(file_input)
        else:
            raise ValueError(f"Unsupported file_input type for PDF extraction: {type(file_input)}")

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text")
            pages.append({
                "page_number": page_idx + 1,
                "text": page_text or "",
            })

        doc.close()
        logger.info(f"Successfully extracted {len(pages)} pages from PDF")
        return pages

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise
