from typing import Any, Dict, List, Tuple
from app.models.fact_registry import FactRegistry
from ai_services.domains.domain_router import domain_router

INTERNAL_TERMS = {
    "contentforge", "pdf extraction", "chunking", "embeddings", "rag retrieval",
    "fact registry", "version 1.0", "synthetic test document", "file-processing",
    "vector database", "traceability pipeline", "multi-format content generation"
}


def build_generator_context(
    facts: List[FactRegistry],
    output_type: str,
    settings: Dict[str, Any],
    domain_key: str = "general",
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Construct a structured, output-tailored representation of facts from the Fact Registry.
    1. Filters out internal system/processing metadata facts.
    2. Ranks facts by importance (HIGH > MEDIUM > LOW) and domain-relevance.
    3. Customizes fact ordering based on output format, audience, detail level, and domain pack.
    """
    filtered_facts: List[FactRegistry] = []
    combined_fact_text = " ".join(f.fact_statement for f in facts)

    # Detect or confirm domain pack
    if domain_key == "general":
        detected_key, _, score = domain_router.detect_domain(combined_fact_text)
        if score >= 0.3:
            domain_key = detected_key

    domain_pack = domain_router.get_domain(domain_key)

    for f in facts:
        stmt_lower = f.fact_statement.lower()
        importance = getattr(f, "importance", "high")
        fact_type = getattr(f, "fact_type", "incident_finding")

        # Exclude internal processing and system metadata facts
        if importance in ("internal", "metadata") or fact_type in ("internal_processing", "document_metadata"):
            continue
        if any(term in stmt_lower for term in INTERNAL_TERMS):
            continue
        filtered_facts.append(f)

    # Fallback to all facts if filtering was overly aggressive
    if not filtered_facts:
        filtered_facts = [f for f in facts if not any(term in f.fact_statement.lower() for term in INTERNAL_TERMS)]
    if not filtered_facts:
        filtered_facts = facts

    # Calculate domain relevance score for each fact
    def _fact_rank_score(f: FactRegistry) -> Tuple[int, int, str]:
        imp_rank = {"high": 0, "medium": 1, "low": 2}.get(getattr(f, "importance", "high"), 0)
        domain_entities = domain_pack.extract_domain_entities(f.fact_statement)
        has_domain_entities = sum(len(v) for v in domain_entities.values()) > 0
        domain_rank = 0 if has_domain_entities else 1
        return (domain_rank, imp_rank, f.fact_id_string)

    filtered_facts.sort(key=_fact_rank_score)

    # Format output-specific selection & depth
    detail_level = settings.get("detail_level", "standard").lower()
    max_facts = 12 if detail_level == "comprehensive" else (8 if detail_level == "standard" else 5)
    selected_facts = filtered_facts[:max_facts]

    raw_facts = []
    formatted_lines = []

    for f in selected_facts:
        fact_dict = {
            "fact_id_string": f.fact_id_string,
            "fact_statement": f.fact_statement,
            "source_snippet": f.source_snippet,
            "confidence": f.confidence,
            "importance": getattr(f, "importance", "high"),
            "fact_type": getattr(f, "fact_type", "incident_finding"),
            "certainty_status": getattr(f, "certainty_status", "confirmed"),
            "entities": getattr(f, "entities", []) or [],
            "dates": getattr(f, "dates", []) or [],
            "numbers": getattr(f, "numbers", []) or [],
            "domain_key": domain_key,
        }
        raw_facts.append(fact_dict)

        certainty_note = f" (Status: {fact_dict['certainty_status']})" if fact_dict['certainty_status'] != "confirmed" else ""
        formatted_lines.append(
            f"- [{f.fact_id_string}] (Type: {fact_dict['fact_type']}, Importance: {fact_dict['importance']}){certainty_note}: "
            f"{f.fact_statement}"
        )

    formatted_facts = "\n".join(formatted_lines)
    return formatted_facts, raw_facts


