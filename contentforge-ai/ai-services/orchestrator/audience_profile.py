import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

AUDIENCE_TYPES = ["technical", "executive", "professional", "general_public"]

AUTOMATIC_AUDIENCE_DEFAULTS: Dict[str, str] = {
    "linkedin": "professional",
    "twitter": "professional",
    "advisory": "technical",
    "executive_summary": "executive",
    "presentation": "professional",
    "video_package": "professional",
    "infographic": "professional",
}

AUDIENCE_PROFILES: Dict[str, Dict[str, Any]] = {
    "technical": {
        "label": "Technical",
        "description": "For technical specialists and engineers. Preserves exact code, version numbers, CVE/CWE identifiers, hashes, and detailed technical mechanisms.",
        "instructions": (
            "AUDIENCE TARGET: Technical Specialists & Engineers.\n"
            "1. Preserve all technical terms, exact version numbers, CVE/CWE identifiers, IP addresses, hashes, and API methods.\n"
            "2. Maintain high information density and detailed technical explanation where supported by source facts.\n"
            "3. Do NOT omit critical technical context or parameters."
        ),
    },
    "executive": {
        "label": "Executive",
        "description": "For C-suite and decision makers. Focuses on strategic impact, risk, and key findings while removing unnecessary implementation details.",
        "instructions": (
            "AUDIENCE TARGET: Executive Leadership & C-Suite.\n"
            "1. Focus on high-level operational impact, risk, key findings, and recommended strategic actions.\n"
            "2. Reduce low-level technical implementation details, but keep all exact numbers, dates, affected entities, and certainty status.\n"
            "3. Use clear, authoritative business language."
        ),
    },
    "professional": {
        "label": "Professional",
        "description": "For general business professionals and broad industry audiences. Balanced technical depth with high readability.",
        "instructions": (
            "AUDIENCE TARGET: General Business & Industry Professionals.\n"
            "1. Maintain a balanced level of technical detail with clear, professional language.\n"
            "2. Retain important technical identifiers and facts, avoiding obscure jargon without oversimplifying.\n"
            "3. Ensure high readability for professional publishing."
        ),
    },
    "general_public": {
        "label": "General Public",
        "description": "For non-technical audiences. Simplifies complex jargon while strictly preserving underlying facts, numbers, and certainty.",
        "instructions": (
            "AUDIENCE TARGET: General Public / Non-Technical Audience.\n"
            "1. Use simple, accessible language and explain technical concepts clearly.\n"
            "2. Reduce unnecessary technical jargon, but STRICTLY PRESERVE all underlying numbers, dates, names, status, and certainty.\n"
            "3. Do NOT change certainty (e.g., 'may' must remain 'may', not 'will')."
        ),
    },
}


def get_audience_profile(audience: str = "professional") -> Dict[str, Any]:
    """Retrieve Audience Profile dictionary for a given audience identifier."""
    aud_clean = (audience or "professional").lower().strip()
    return AUDIENCE_PROFILES.get(aud_clean, AUDIENCE_PROFILES["professional"])


def normalize_audience_key(aud: str) -> str:
    aud_clean = (aud or "").lower().strip()
    if "exec" in aud_clean or "c-suite" in aud_clean:
        return "executive"
    if "tech" in aud_clean:
        return "technical"
    if "public" in aud_clean:
        return "general_public"
    if "prof" in aud_clean or "auto" in aud_clean:
        return "professional"
    return AUDIENCE_TYPES[2] if aud_clean not in AUDIENCE_PROFILES else aud_clean


def resolve_audiences(
    selected_outputs: List[str],
    selected_audiences: List[str],
) -> List[Dict[str, str]]:
    """
    Resolve requested outputs and audiences into (output_type, audience_type) pairs.
    If 'automatic' (or empty) is present in selected_audiences, maps each output format
    to its optimal default audience.
    """
    is_auto = not selected_audiences or "automatic" in [a.lower() for a in selected_audiences]
    pairs = []

    if is_auto:
        for out in selected_outputs:
            auto_aud = AUTOMATIC_AUDIENCE_DEFAULTS.get(out.lower(), "professional")
            pairs.append({"output_type": out.lower(), "audience": auto_aud})
    else:
        for out in selected_outputs:
            for aud in selected_audiences:
                aud_clean = normalize_audience_key(aud)
                pairs.append({"output_type": out.lower(), "audience": aud_clean})

    return pairs
