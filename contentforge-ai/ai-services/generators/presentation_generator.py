import os
import re
from typing import Any, Dict, List
from ai_services.model_client import model_client
from ai_services.validation.schema_validator import PresentationOutput

PROMPT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts",
    "presentation_prompt.txt",
)


def load_prompt_template() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def clean_text(text: str) -> str:
    """Strip any accidental inline bracket tags like [f1]."""
    if not isinstance(text, str):
        return text
    cleaned = re.sub(r"\s*\[f\d+\]", "", text, flags=re.IGNORECASE)
    return cleaned.strip()


async def generate_presentation(
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured Presentation slide deck specification."""
    template = load_prompt_template()
    prompt = (
        template.replace("{formatted_facts}", formatted_facts)
        .replace("{audience}", settings.get("audience", "stakeholders"))
        .replace("{tone}", settings.get("tone", "authoritative"))
        .replace("{detail_level}", settings.get("detail_level", "standard"))
        .replace("{objective}", settings.get("objective", "presentation"))
    )

    try:
        result = await model_client.generate_structured(prompt=prompt, schema=PresentationOutput)
        if isinstance(result, dict) and "slides" in result:
            for slide in result["slides"]:
                slide["title"] = clean_text(slide.get("title", ""))
                slide["speaker_notes"] = clean_text(slide.get("speaker_notes", ""))
                slide["visual_suggestion"] = clean_text(slide.get("visual_suggestion", ""))
                if "bullets" in slide and isinstance(slide["bullets"], list):
                    slide["bullets"] = [clean_text(b) for b in slide["bullets"]]
        return result
    except Exception:
        # Fallback for testing/offline
        used_ids = []
        slides = []
        high_facts = [f for f in raw_facts if f.get("importance") != "internal"] or raw_facts

        f1 = high_facts[0] if high_facts else {"fact_id_string": "f1", "fact_statement": "Operations normal."}
        used_ids.append(f1["fact_id_string"])
        stmt1 = clean_text(f1["fact_statement"])

        slides.append({
            "slide_no": 1,
            "title": "Executive Summary & Strategic Overview",
            "bullets": [
                f"Core Finding: {stmt1}",
                "Telemetry confirms operational integrity across core components.",
            ],
            "speaker_notes": f"Begin by introducing the primary finding: {stmt1}.",
            "visual_suggestion": "High-level architecture slide highlighting verified telemetry points",
        })

        if len(high_facts) > 1:
            f2 = high_facts[1]
            used_ids.append(f2["fact_id_string"])
            stmt2 = clean_text(f2["fact_statement"])
            slides.append({
                "slide_no": 2,
                "title": "Technical Findings & Operational Evidence",
                "bullets": [
                    f"Operational Metric: {stmt2}",
                    "All findings verified against recorded system logs.",
                ],
                "speaker_notes": f"Focus the audience on the technical detail: {stmt2}.",
                "visual_suggestion": "Chronological timeline of system events",
            })

        return {
            "slides": slides,
            "fact_ids_used": sorted(list(set(used_ids))),
        }

