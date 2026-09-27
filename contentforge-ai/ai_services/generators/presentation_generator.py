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


def extract_requested_slide_count(settings: Dict[str, Any]) -> int:
    """Determine target slide count (default = 5) from settings or user request text."""
    if not settings:
        return 5
    if "slide_count" in settings and settings["slide_count"]:
        try:
            return max(1, min(20, int(settings["slide_count"])))
        except (ValueError, TypeError):
            pass
    if "requested_slide_count" in settings and settings["requested_slide_count"]:
        try:
            return max(1, min(20, int(settings["requested_slide_count"])))
        except (ValueError, TypeError):
            pass

    # Natural language parsing
    search_text = " ".join([
        str(settings.get("prompt", "")),
        str(settings.get("objective", "")),
        str(settings.get("user_request", "")),
    ])
    match = re.search(r"\b(\d{1,2})\s*-?\s*slides?\b", search_text, re.IGNORECASE)
    if match:
        try:
            val = int(match.group(1))
            return max(1, min(20, val))
        except ValueError:
            pass

    return 5  # ContentX Default = 5 slides


async def generate_presentation(
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured Presentation slide deck specification with default 5 slides or custom count."""
    template = load_prompt_template()
    requested_slides = extract_requested_slide_count(settings)

    prompt = (
        template.replace("{formatted_facts}", formatted_facts)
        .replace("{audience}", settings.get("audience", "stakeholders"))
        .replace("{tone}", settings.get("tone", "authoritative"))
        .replace("{detail_level}", settings.get("detail_level", "standard"))
        .replace("{objective}", settings.get("objective", "presentation"))
    )
    prompt += f"\n\nCRITICAL CONSTRAINT: Generate EXACTLY {requested_slides} slides in the slides array."

    domain_key = "general"
    if raw_facts and isinstance(raw_facts, list):
        domain_key = raw_facts[0].get("domain_key", "general")

    try:
        result = await model_client.generate_structured(prompt=prompt, schema=PresentationOutput)
        if isinstance(result, dict) and "slides" in result:
            slides = result.get("slides", [])
            high_facts = [
                f for f in raw_facts 
                if f.get("importance") not in ("internal", "metadata") 
                and f.get("fact_type") not in ("internal_processing", "document_metadata")
            ] or raw_facts

            # Enforce exact requested_slides count
            if len(slides) < requested_slides:
                start_len = len(slides)
                for idx in range(start_len, requested_slides):
                    fact = high_facts[idx % len(high_facts)]
                    stmt = clean_text(fact.get("fact_statement", ""))
                    slides.append({
                        "slide_no": idx + 1,
                        "title": f"Key Analysis & Supporting Details — Part {idx - start_len + 1}",
                        "bullets": [
                            f"Verified Point: {stmt}",
                            "Evidence supported strictly by source document Fact Registry.",
                        ],
                        "speaker_notes": f"Highlight to audience: {stmt}",
                        "visual_suggestion": f"Diagram illustrating key finding {idx + 1}.",
                    })
            elif len(slides) > requested_slides:
                slides = slides[:requested_slides]

            for idx, slide in enumerate(slides):
                slide["slide_no"] = idx + 1
                slide["title"] = clean_text(slide.get("title", ""))
                slide["speaker_notes"] = clean_text(slide.get("speaker_notes", ""))
                slide["visual_suggestion"] = clean_text(slide.get("visual_suggestion", ""))
                if "bullets" in slide and isinstance(slide["bullets"], list):
                    slide["bullets"] = [clean_text(b) for b in slide["bullets"]]

            result["slides"] = slides
            result["requested_slide_count"] = requested_slides
            result["actual_slide_count"] = len(slides)
        return result
    except Exception:
        # Domain-aware fallback slide deck engine generating EXACTLY requested_slides count
        high_facts = [
            f for f in raw_facts 
            if f.get("importance") not in ("internal", "metadata") 
            and f.get("fact_type") not in ("internal_processing", "document_metadata")
        ] or raw_facts

        used_ids = []
        slides = []

        slide_titles = [
            "Executive Overview & Core Focus",
            "Background & Context",
            "Key Verified Findings",
            "Operational Analysis & Impact",
            "Conclusion & Source-Supported Next Steps"
        ]

        if domain_key == "research":
            slide_titles = [
                "Research Overview & Objective",
                "Dataset & Methodology Context",
                "Key Model Findings & Results",
                "Performance Analysis & Impact",
                "Summary & Technical Next Steps"
            ]
        elif domain_key == "cybersecurity":
            slide_titles = [
                "Advisory Overview",
                "Threat & System Context",
                "Key Security Findings",
                "Impact Analysis",
                "Mitigation & Recommended Actions"
            ]

        # Generate N slides matching requested_slides
        for idx in range(requested_slides):
            slide_no = idx + 1
            fact = high_facts[idx % len(high_facts)]
            fid = fact.get("fact_id_string", f"f{idx+1}")
            used_ids.append(fid)
            stmt = clean_text(fact.get("fact_statement", ""))

            title = slide_titles[idx] if idx < len(slide_titles) else f"Supporting Details — Part {idx - len(slide_titles) + 2}"

            slides.append({
                "slide_no": slide_no,
                "title": title,
                "bullets": [
                    f"Verified Point: {stmt}",
                    "Evidence supported strictly by source document Fact Registry.",
                ],
                "speaker_notes": f"Highlight to audience: {stmt}",
                "visual_suggestion": f"Diagram illustrating slide {slide_no} metrics.",
            })

        first_stmt = high_facts[0].get("fact_statement", "") if high_facts else ""
        main_topic = first_stmt.split(" ")[0] if first_stmt else "Strategic"

        return {
            "requested_slide_count": requested_slides,
            "actual_slide_count": len(slides),
            "title": f"{main_topic} Executive Presentation",
            "slides": slides,
            "fact_ids_used": sorted(list(set(used_ids))),
        }
