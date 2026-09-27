import re
from typing import Any, Dict, List, Tuple
from app.models.fact_registry import FactRegistry
from ai_services.domains.domain_router import domain_router

INTERNAL_TERMS = {
    "contentforge", "pdf extraction", "chunking", "embeddings", "rag retrieval",
    "fact registry", "version 1.0", "synthetic test document", "file-processing",
    "vector database", "traceability pipeline", "multi-format content generation"
}

EXTRACTION_NOISE_TERMS = {
    "page 1 of", "page 2 of", "page 3 of", "page 4 of", "page 5 of", "predictions.csv",
    "total marks:", "submission: code", "submission instructions"
}


def build_generator_context(
    facts: List[FactRegistry],
    output_type: str,
    settings: Dict[str, Any],
    domain_key: str = "general",
    audience: str = "professional",
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Construct a structured, output-tailored representation of facts from the Fact Registry.
    1. Filters out internal system/processing metadata facts and extraction noise.
    2. Ranks facts by importance (HIGH > MEDIUM > LOW) and domain-relevance.
    3. Customizes fact ordering based on output format, audience, detail level, and domain pack.
    4. Applies Truth Compression Audience Profile context instructions without altering approved generator prompts.
    """
    from ai_services.orchestrator.audience_profile import get_audience_profile

    filtered_facts: List[FactRegistry] = []
    combined_fact_text = " ".join(f.fact_statement for f in facts)

    # Detect or confirm domain pack
    if domain_key == "general":
        detected_key, _, score = domain_router.detect_domain(combined_fact_text)
        if score >= 0.25:
            domain_key = detected_key

    domain_pack = domain_router.get_domain(domain_key)

    for f in facts:
        stmt_lower = f.fact_statement.lower()
        importance = getattr(f, "importance", "high")
        fact_type = getattr(f, "fact_type", "incident_finding")

        # Exclude internal processing, document metadata, and raw extraction noise
        if importance in ("internal", "metadata") or fact_type in ("internal_processing", "document_metadata"):
            continue
        if any(term in stmt_lower for term in INTERNAL_TERMS) or any(noise in stmt_lower for noise in EXTRACTION_NOISE_TERMS):
            continue
        if re.search(r"\bpage\s+\d+\s+of\s+\d+\b", stmt_lower):
            continue
        filtered_facts.append(f)

    # Fallback to all facts if filtering was overly aggressive
    if not filtered_facts:
        filtered_facts = [f for f in facts if not any(term in f.fact_statement.lower() for term in INTERNAL_TERMS)]
    if not filtered_facts:
        filtered_facts = facts

    # Centralized Output-Specific Fact Caps
    OUTPUT_FACT_CAPS = {
        "linkedin": 8,
        "twitter": 6,
        "executive_summary": 12,
        "advisory": 8,
        "presentation": 15,
        "infographic": 8,
        "video_package": 8,
    }

    # Calculate domain and output-specific relevance score for each fact
    def _fact_rank_score(f: FactRegistry) -> Tuple[int, int, int, str]:
        # Importance ordering is FIRST priority: HIGH (0) > MEDIUM (1) > LOW (2)
        imp_map = {"high": 0, "medium": 1, "low": 2}
        f_imp = getattr(f, "importance", "high") or "high"
        imp_rank = imp_map.get(str(f_imp).lower(), 0)

        stmt_lower = f.fact_statement.lower()

        out_rel = 1
        if output_type == "advisory":
            advisory_kws = {"vulnerability", "cve", "threat", "affected", "impact", "mitigation", "severity", "security", "attack", "exploit"}
            if any(k in stmt_lower for k in advisory_kws):
                out_rel = 0
        elif output_type == "executive_summary":
            exec_kws = {"finding", "impact", "result", "status", "action", "unresolved", "overall", "key", "strategic", "summary"}
            if any(k in stmt_lower for k in exec_kws):
                out_rel = 0
        elif output_type == "presentation":
            ppt_kws = {"overview", "background", "finding", "result", "analysis", "impact", "action", "next", "conclusion"}
            if any(k in stmt_lower for k in ppt_kws):
                out_rel = 0

        domain_entities = domain_pack.extract_domain_entities(f.fact_statement)
        has_domain_entities = sum(len(v) for v in domain_entities.values()) > 0
        domain_rank = 0 if has_domain_entities else 1

        # Priority order: Importance Tier -> Output Relevance -> Domain Entity Relevance -> Fact ID tie-breaker
        return (imp_rank, out_rel, domain_rank, f.fact_id_string)

    filtered_facts.sort(key=_fact_rank_score)

    # Output-specific dynamic selection & depth
    detail_level = settings.get("detail_level", "standard").lower()
    base_cap = OUTPUT_FACT_CAPS.get(output_type.lower().strip(), 8)
    if detail_level == "comprehensive":
        max_facts = min(base_cap + 3, 15)
    elif detail_level == "concise":
        max_facts = max(base_cap - 2, 4)
    else:
        max_facts = base_cap

    selected_facts = filtered_facts[:max_facts]

    # Diagnostic Logging
    import logging
    c_logger = logging.getLogger(__name__)
    high_cnt = sum(1 for f in facts if getattr(f, "importance", "high") == "high")
    med_cnt = sum(1 for f in facts if getattr(f, "importance", "high") == "medium")
    low_cnt = sum(1 for f in facts if getattr(f, "importance", "high") == "low")
    sel_high = sum(1 for f in selected_facts if getattr(f, "importance", "high") == "high")
    sel_med = sum(1 for f in selected_facts if getattr(f, "importance", "high") == "medium")
    sel_low = sum(1 for f in selected_facts if getattr(f, "importance", "high") == "low")

    c_logger.info(
        f"CONTEXT SELECTION | OUTPUT TYPE: {output_type} | AVAILABLE FACTS: {len(facts)} | "
        f"HIGH: {high_cnt} | MEDIUM: {med_cnt} | LOW: {low_cnt} | CONTEXT CAP: {max_facts} | "
        f"SELECTED: {len(selected_facts)} | SELECTED HIGH: {sel_high} | SELECTED MEDIUM: {sel_med} | SELECTED LOW: {sel_low}"
    )

    raw_facts = []
    formatted_lines = []

    # Get Audience Profile instructions
    profile = get_audience_profile(audience)
    formatted_lines.append(f"=== TRUTH COMPRESSION AUDIENCE CONTEXT ===")
    formatted_lines.append(f"Target Audience: {profile['label']}")
    formatted_lines.append(f"{profile['instructions']}")
    formatted_lines.append(f"\n=== FACT REGISTRY (Grounding Facts - preserve all exact numbers, dates, entities, technical IDs, status, and certainty) ===")

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
            "target_audience": audience,
        }
        raw_facts.append(fact_dict)

        certainty_note = f" (Status: {fact_dict['certainty_status']})" if fact_dict['certainty_status'] != "confirmed" else ""
        formatted_lines.append(
            f"- [{f.fact_id_string}] (Type: {fact_dict['fact_type']}, Importance: {fact_dict['importance']}){certainty_note}: "
            f"{f.fact_statement}"
        )

    formatted_facts = "\n".join(formatted_lines)
    return formatted_facts, raw_facts


