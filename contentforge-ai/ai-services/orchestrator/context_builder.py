import re
from typing import Any, Dict, List, Tuple, Optional
from app.models.fact_registry import FactRegistry
from ai_services.domains.domain_router import domain_router
from ai_services.retrieval.content_filter import classify_content_text

INTERNAL_TERMS = {
    "contentforge", "pdf extraction", "chunking", "embeddings", "rag retrieval",
    "fact registry", "version 1.0", "synthetic test document", "file-processing",
    "vector database", "traceability pipeline", "multi-format content generation"
}

EXTRACTION_NOISE_TERMS = {
    "page 1 of", "page 2 of", "page 3 of", "page 4 of", "page 5 of", "predictions.csv",
    "total marks:", "submission: code", "submission instructions"
}

METADATA_DISCLAIMER_TERMS = {
    "copyright", "all rights reserved", "cashflow technologies", "plata publishing",
    "isbn", "printed in", "stolen property", "disclaim any liability", "legal or other expert assistance"
}


def build_generator_context(
    facts: List[FactRegistry],
    output_type: str,
    settings: Dict[str, Any],
    domain_key: str = "general",
    audience: str = "professional",
    retrieved_chunks: Optional[List[Any]] = None,
    allow_metadata: bool = False,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Construct a structured, output-tailored representation of facts and retrieved source chunks.
    1. Classifies and filters facts by content role (prioritizing core content over copyright/metadata).
    2. Ranks facts by Content Role Weight -> Output Relevance -> Importance Tier.
    3. Integrates retrieved substantive source chunk text alongside Fact Registry facts.
    4. Enforces Truth Compression Audience Profile context instructions.
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
            if not allow_metadata:
                continue
        if any(term in stmt_lower for term in INTERNAL_TERMS) or any(noise in stmt_lower for noise in EXTRACTION_NOISE_TERMS):
            continue
        if re.search(r"\bpage\s+\d+\s+of\s+\d+\b", stmt_lower):
            continue
            
        # Deprioritize copyright/disclaimer text unless explicitly allowed
        if not allow_metadata and any(meta_term in stmt_lower for meta_term in METADATA_DISCLAIMER_TERMS):
            continue

        filtered_facts.append(f)

    # Fallback to all non-internal facts if filtering was overly aggressive
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

    # Calculate content-role and output-specific relevance score for each fact
    def _fact_rank_score(f: FactRegistry) -> Tuple[int, int, int, str]:
        stmt_lower = f.fact_statement.lower()
        content_role = classify_content_text(f.fact_statement)

        # Content Role Tier is FIRST priority (0 = body/chapter, 1 = conclusion, 2 = metadata, 3 = copyright)
        role_map = {"body": 0, "chapter": 0, "section": 0, "conclusion": 1, "introduction": 2, "metadata": 3, "copyright": 4, "noise": 5}
        role_rank = role_map.get(content_role, 1)

        # Output Relevance
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
        elif output_type == "linkedin":
            linkedin_kws = {"rich dad", "poor dad", "financial education", "asset", "liability", "cash flow", "lesson", "principle", "wealth", "investing"}
            if any(k in stmt_lower for k in linkedin_kws):
                out_rel = 0

        # Importance Tier: HIGH (0) > MEDIUM (1) > LOW (2)
        imp_map = {"high": 0, "medium": 1, "low": 2}
        f_imp = getattr(f, "importance", "high") or "high"
        imp_rank = imp_map.get(str(f_imp).lower(), 0)

        # Priority order: Content Role Tier -> Output Relevance -> Importance Tier -> Fact ID
        return (role_rank, out_rel, imp_rank, f.fact_id_string)

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

    raw_facts = []
    formatted_lines = []

    # Get Audience Profile instructions
    profile = get_audience_profile(audience)
    formatted_lines.append(f"=== TRUTH COMPRESSION AUDIENCE CONTEXT ===")
    formatted_lines.append(f"Target Audience: {profile['label']}")
    formatted_lines.append(f"{profile['instructions']}")

    # Include Retrieved Substantive Chunks if provided
    if retrieved_chunks:
        formatted_lines.append(f"\n=== RETRIEVED SUBSTANTIVE SOURCE CONTENT ===")
        for idx, chunk in enumerate(retrieved_chunks[:5]):
            page_str = f" [Page {chunk.page_number}]" if hasattr(chunk, "page_number") and chunk.page_number else ""
            c_index = getattr(chunk, "chunk_index", idx)
            text_snippet = chunk.text.strip() if hasattr(chunk, "text") else str(chunk)
            formatted_lines.append(f"Source Chunk #{c_index}{page_str}:\n{text_snippet}\n")

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
