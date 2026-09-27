"""ContentForge AI - PII Detection Engine.

Deterministic regex-based scanner for Personally Identifiable Information (PII):
- Email addresses
- Phone numbers (NANP, UK, International E.164)
- Social Security Numbers (SSN)
- Payment card numbers (Visa, Mastercard, Amex with Luhn validation)
- Government ID / Tax ID patterns
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field


class PIIScanResult(BaseModel):
    pii_detected: bool = False
    pii_types: List[str] = Field(default_factory=list)
    match_counts: Dict[str, int] = Field(default_factory=dict)
    sample_matches: Dict[str, List[str]] = Field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pii_detected": self.pii_detected,
            "pii_types": self.pii_types,
            "match_counts": self.match_counts,
        }


# High-precision PII regex rules
PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (
        "email",
        re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "phone",
        re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b"
        ),
    ),
    (
        "ssn",
        re.compile(
            r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"
        ),
    ),
    (
        "credit_card",
        re.compile(
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"
        ),
    ),
    (
        "id_number",
        re.compile(
            r"\b(?:TAXID|EIN|PASSPORT|SSN|TIN)[\s:#-]*[A-Z0-9]{6,12}\b",
            re.IGNORECASE,
        ),
    ),
]


def luhn_checksum(card_number_str: str) -> bool:
    """Validates payment card numbers via the Luhn algorithm."""
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


def scan_text_for_pii(text: str) -> PIIScanResult:
    """Scans text and returns detected PII categories and counts.

    Args:
        text: Input string (document text, chunk, or metadata).

    Returns:
        PIIScanResult with flags and detected categories.
    """
    if not text or not text.strip():
        return PIIScanResult()

    detected_types: Set[str] = set()
    match_counts: Dict[str, int] = {}
    sample_matches: Dict[str, List[str]] = {}

    for pii_type, pattern in PII_PATTERNS:
        matches = pattern.findall(text)
        valid_matches = []

        for m in matches:
            match_str = m if isinstance(m, str) else m[0]
            # Extra verification for credit cards
            if pii_type == "credit_card":
                clean_num = re.sub(r"[-.\s]", "", match_str)
                if not luhn_checksum(clean_num):
                    continue
            # Filter trivial number sequences for phone
            if pii_type == "phone":
                clean_digits = re.sub(r"\D", "", match_str)
                if len(clean_digits) < 10 or len(clean_digits) > 15:
                    continue
                # Reject repetitive strings like 000-000-0000
                if len(set(clean_digits)) <= 2:
                    continue

            valid_matches.append(match_str)

        if valid_matches:
            detected_types.add(pii_type)
            match_counts[pii_type] = len(valid_matches)
            # Store up to 2 masked samples for audit review
            sample_matches[pii_type] = [
                f"{v[:3]}***{v[-2:]}" if len(v) > 5 else "***"
                for v in valid_matches[:2]
            ]

    pii_detected = len(detected_types) > 0

    return PIIScanResult(
        pii_detected=pii_detected,
        pii_types=sorted(list(detected_types)),
        match_counts=match_counts,
        sample_matches=sample_matches,
    )


def redact_pii_from_text(text: str) -> str:
    """Replaces detected PII instances with standardized redaction tokens."""
    if not text:
        return text

    redacted = text
    for pii_type, pattern in PII_PATTERNS:
        placeholder = f"[{pii_type.upper()}_REDACTED]"
        redacted = pattern.sub(placeholder, redacted)

    return redacted
