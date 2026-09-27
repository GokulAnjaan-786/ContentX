import os
import re
from typing import Any, Dict, List
from ai_services.model_client import model_client
from ai_services.validation.schema_validator import VideoPackageOutput

PROMPT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts",
    "video_prompt.txt",
)


def load_prompt_template() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def clean_scene_text(text: str) -> str:
    """Strip any accidental inline bracket tags like [f1]."""
    if not isinstance(text, str):
        return text
    cleaned = re.sub(r"\s*\[f\d+\]", "", text, flags=re.IGNORECASE)
    return cleaned.strip()


async def generate_video_package(
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured Video Script Package (scenes, narration, timings)."""
    template = load_prompt_template()
    prompt = (
        template.replace("{formatted_facts}", formatted_facts)
        .replace("{audience}", settings.get("audience", "general_public"))
        .replace("{tone}", settings.get("tone", "dynamic"))
        .replace("{detail_level}", settings.get("detail_level", "standard"))
        .replace("{objective}", settings.get("objective", "explainer"))
    )

    domain_key = "general"
    if raw_facts and isinstance(raw_facts, list):
        domain_key = raw_facts[0].get("domain_key", "general")

    try:
        result = await model_client.generate_structured(prompt=prompt, schema=VideoPackageOutput)
        if isinstance(result, dict) and "scenes" in result:
            for scene in result["scenes"]:
                scene["narration"] = clean_scene_text(scene.get("narration", ""))
                scene["visual_description"] = clean_scene_text(scene.get("visual_description", ""))
                scene["subtitle_text"] = clean_scene_text(scene.get("subtitle_text", ""))
            result["title"] = clean_scene_text(result.get("title", ""))
        return result
    except Exception:
        # Domain-aware fallback generator
        used_ids = []
        scenes = []
        high_facts = [
            f for f in raw_facts 
            if f.get("importance") not in ("internal", "metadata") 
            and f.get("fact_type") not in ("internal_processing", "document_metadata")
        ] or raw_facts

        for i, fact in enumerate(high_facts[:3], start=1):
            fid = fact["fact_id_string"]
            used_ids.append(fid)
            stmt = fact.get("fact_statement", "").rstrip(".")

            if domain_key == "research":
                if i == 1:
                    narration = f"Analysis confirmed key technical findings when {stmt.lower()}."
                    visual = "Data science workflow diagram displaying evaluation metrics."
                elif i == 2:
                    narration = f"Model evaluation verified that {stmt.lower()}."
                    visual = "Interactive performance metric chart highlighting model outputs."
                else:
                    narration = f"Applying verified methodologies established that {stmt.lower()}."
                    visual = "Technical summary dashboard displaying final results."
            elif domain_key == "cybersecurity":
                if i == 1:
                    narration = f"Security monitoring detected operational findings when {stmt.lower()}."
                    visual = "Security dashboard illustrating telemetry indicators."
                elif i == 2:
                    narration = f"Technical analysis confirmed that {stmt.lower()}."
                    visual = "Network diagram animation showing system flow."
                else:
                    narration = f"Response protocols verified that {stmt.lower()}."
                    visual = "Remediation status checklist."
            else:
                if i == 1:
                    narration = f"Overview analysis established that {stmt.lower()}."
                    visual = "Executive overview presentation slide."
                elif i == 2:
                    narration = f"Detailed evaluation verified that {stmt.lower()}."
                    visual = "Data visualization graph showing key metrics."
                else:
                    narration = f"Operational review confirmed that {stmt.lower()}."
                    visual = "Summary takeaway dashboard."

            scenes.append({
                "scene_no": i,
                "narration": narration,
                "visual_description": visual,
                "subtitle_text": stmt[:90],
                "duration_estimate_sec": 12,
            })

        if not scenes:
            scenes = [{
                "scene_no": 1,
                "narration": "Technical analysis provided verified operational insights.",
                "visual_description": "Clean presentation slide displaying summary data.",
                "subtitle_text": "Operational overview and findings.",
                "duration_estimate_sec": 10,
            }]
            used_ids = ["f1"]

        title_label = "Research & Technical Briefing" if domain_key == "research" else ("Security Advisory Briefing" if domain_key == "cybersecurity" else "Operational Technical Briefing")

        return {
            "title": title_label,
            "total_duration_estimate": f"{len(scenes) * 12}s",
            "scenes": scenes,
            "fact_ids_used": sorted(list(set(used_ids))),
        }
