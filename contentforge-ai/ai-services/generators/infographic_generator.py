import os
import re
from typing import Any, Dict, List
from ai_services.model_client import model_client
from ai_services.validation.schema_validator import InfographicOutput

PROMPT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts",
    "infographic_prompt.txt",
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


async def generate_infographic(
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured Infographic content and layout specifications."""
    template = load_prompt_template()
    prompt = (
        template.replace("{formatted_facts}", formatted_facts)
        .replace("{audience}", settings.get("audience", "general_public"))
        .replace("{tone}", settings.get("tone", "engaging"))
        .replace("{detail_level}", settings.get("detail_level", "standard"))
        .replace("{objective}", settings.get("objective", "visual_summary"))
    )

    try:
        result = await model_client.generate_structured(prompt=prompt, schema=InfographicOutput)
        if isinstance(result, dict):
            result["headline"] = clean_text(result.get("headline", ""))
            if "sections" in result and isinstance(result["sections"], list):
                for s in result["sections"]:
                    s["stat_or_point"] = clean_text(s.get("stat_or_point", ""))
        return result
    except Exception:
        # Fallback for testing/offline
        used_ids = []
        sections = []
        high_facts = [f for f in raw_facts if f.get("importance") != "internal"] or raw_facts

        for i, fact in enumerate(high_facts[:3], start=1):
            fid = fact["fact_id_string"]
            used_ids.append(fid)
            stmt = clean_text(fact['fact_statement'])
            sections.append({
                "order": i,
                "stat_or_point": stmt,
                "icon_suggestion": "shield-check" if i == 1 else ("trending-up" if i == 2 else "alert-triangle"),
            })

        if not sections:
            sections = [{"order": 1, "stat_or_point": "Security operations status verified.", "icon_suggestion": "shield-check"}]
            used_ids = ["f1"]

        first_entity = high_facts[0].get("entities", ["System"])[0] if high_facts and high_facts[0].get("entities") else "System"

        return {
            "headline": f"{first_entity} Incident Summary & Key Telemetry",
            "sections": sections,
            "layout_style": "3-card-horizontal",
            "colour_theme": "navy-and-cyan",
            "fact_ids_used": sorted(list(set(used_ids))),
        }

