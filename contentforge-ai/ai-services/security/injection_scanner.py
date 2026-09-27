"""ContentForge AI - Prompt Injection Scanner.

Performs deterministic heuristic & regex scanning for known adversarial prompt injection,
jailbreak, role-hijack, and delimiter evasion patterns before content enters the
AI Understanding Pass.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Tuple
from pydantic import BaseModel, Field


class InjectionMatch(BaseModel):
    category: str
    pattern_name: str
    snippet: str
    severity: str  # "low", "medium", "high", "critical"


class InjectionScanResult(BaseModel):
    is_flagged: bool = False
    risk_score: float = 0.0  # 0.0 (safe) to 1.0 (extreme danger)
    risk_level: str = "none"  # "none", "low", "medium", "high", "critical"
    matches: List[InjectionMatch] = Field(default_factory=list)
    detected_patterns: List[str] = Field(default_factory=list)
    warning_message: str | None = None
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "is_flagged": self.is_flagged,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "detected_patterns": self.detected_patterns,
            "warning_message": self.warning_message,
            "match_count": len(self.matches),
            "scanned_at": self.scanned_at.isoformat(),
        }


# Compiled regex patterns classified by attack vector
INJECTION_RULES: List[Tuple[str, str, str, re.Pattern]] = [
    # 1. Direct Instruction Overrides (Critical)
    (
        "Direct Override",
        "ignore_instructions",
        "critical",
        re.compile(
            r"(?:ignore|disregard|forget|skip|override|bypass)\s+(?:all\s+)?(?:previous|above|prior|system)\s+(?:instructions|prompts|rules|commands|constraints|directives)",
            re.IGNORECASE,
        ),
    ),
    (
        "Direct Override",
        "do_not_follow_rules",
        "critical",
        re.compile(
            r"(?:do\s+not|don't)\s+follow\s+(?:the\s+)?(?:system|previous|above|original)\s+(?:instructions|rules)",
            re.IGNORECASE,
        ),
    ),
    # 2. Persona Hijack / Jailbreaks (High)
    (
        "Persona Hijack",
        "you_are_now",
        "high",
        re.compile(
            r"(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|simulate|roleplay\s+as)\s+(?:a|an)?\s*(?:DAN|unrestricted|jailbreak|evil|hacker|root|administrator|developer\s+mode|gpt-\d+\s+unfiltered)",
            re.IGNORECASE,
        ),
    ),
    (
        "Persona Hijack",
        "jailbreak_phrase",
        "high",
        re.compile(
            r"\b(?:DAN\s+mode|jailbreak|always\s+say\s+yes|bypass\s+safety\s+filters|freedom\s+mode)\b",
            re.IGNORECASE,
        ),
    ),
    # 3. Delimiter Escapes & Special Tokens (Critical)
    (
        "Delimiter Escape",
        "fake_delimiter_close",
        "critical",
        re.compile(
            r"<\s*/\s*(?:source_document|fact_registry|document_content|system|context)\s*>",
            re.IGNORECASE,
        ),
    ),
    (
        "Delimiter Escape",
        "special_tokens",
        "critical",
        re.compile(
            r"(?:<\|im_start\|>|<\|im_end\|>|<\|system\|>|\[SYSTEM\]|\[INST\]|\[/INST\]|<s>|</s>)",
            re.IGNORECASE,
        ),
    ),
    # 4. System Prompt Leaking (Medium)
    (
        "Prompt Leak",
        "leak_system_prompt",
        "medium",
        re.compile(
            r"(?:repeat|show|print|reveal|output|display|tell\s+me)\s+(?:the\s+)?(?:system\s+prompt|initial\s+instructions|secret\s+key|internal\s+instructions|system\s+message)",
            re.IGNORECASE,
        ),
    ),
    # 5. Output Format Manipulation (Medium)
    (
        "Format Manipulation",
        "force_json_hijack",
        "medium",
        re.compile(
            r"(?:instead\s+of\s+json|do\s+not\s+output\s+json|format\s+as\s+plain\s+text\s+instead|ignore\s+json\s+schema)",
            re.IGNORECASE,
        ),
    ),
]


def scan_for_prompt_injection(text: str) -> InjectionScanResult:
    """Scans raw or chunked document text for known prompt injection patterns.

    Args:
        text: Raw document text to scan.

    Returns:
        InjectionScanResult with risk assessment, matched snippets, and warnings.
    """
    if not text or not text.strip():
        return InjectionScanResult()

    matches: List[InjectionMatch] = []
    pattern_names: List[str] = []
    total_weight = 0.0

    severity_weights = {
        "low": 0.2,
        "medium": 0.4,
        "high": 0.7,
        "critical": 1.0,
    }

    for category, pattern_name, severity, pattern in INJECTION_RULES:
        for match in pattern.finditer(text):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            snippet = text[start:end].replace("\n", " ").strip()

            matches.append(
                InjectionMatch(
                    category=category,
                    pattern_name=pattern_name,
                    snippet=f"...{snippet}...",
                    severity=severity,
                )
            )
            if pattern_name not in pattern_names:
                pattern_names.append(pattern_name)
            total_weight += severity_weights.get(severity, 0.3)

    if not matches:
        return InjectionScanResult()

    # Calculate bounded risk score between 0.0 and 1.0
    risk_score = min(1.0, round(total_weight, 2))

    if risk_score >= 0.8:
        risk_level = "critical"
    elif risk_score >= 0.5:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    warning_msg = (
        f"Potential adversarial prompt injection detected ({len(matches)} match(es), "
        f"risk: {risk_level.upper()}). Patterns: {', '.join(pattern_names[:3])}."
    )

    return InjectionScanResult(
        is_flagged=True,
        risk_score=risk_score,
        risk_level=risk_level,
        matches=matches,
        detected_patterns=pattern_names,
        warning_message=warning_msg,
    )


def sanitize_document_delimiters(text: str) -> str:
    """Neutralizes adversarial delimiter closing tags in raw content.

    Prevents attacks attempting to break out of `<source_document>` or `<fact_registry>` tags.
    """
    if not text:
        return text

    # Escape closing tags by replacing angle brackets
    text = re.sub(
        r"<\s*/\s*(source_document|fact_registry|system|context)\s*>",
        r"[ESCAPED_DELIMITER_TAG: \1]",
        text,
        flags=re.IGNORECASE,
    )
    # Neutralize special chat tokens
    text = re.sub(
        r"<\|(im_start|im_end|system)\|>",
        r"[ESCAPED_SPECIAL_TOKEN: \1]",
        text,
        flags=re.IGNORECASE,
    )
    return text
