import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

CITATION_REGEX = re.compile(r"\[(f\d+)\]", re.IGNORECASE)
DATE_REGEX = re.compile(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)
NUMBER_REGEX = re.compile(r"\b\d+(?:[\.,]\d+)?%?\b")


def extract_claims_and_citations(content: Any) -> List[Tuple[str, List[str]]]:
    """
    Traverse a structured output dictionary and extract individual claims
    along with their embedded [fX] citations.
    """
    claims: List[Tuple[str, List[str]]] = []

    def _traverse(node: Any):
        if isinstance(node, str):
            # Split into individual sentences or clauses
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", node) if s.strip()]
            for sentence in sentences:
                # Ignore hashtag lists, brief labels, or layout keywords
                if sentence.startswith("#") or len(sentence.split()) < 3:
                    continue
                found_citations = CITATION_REGEX.findall(sentence)
                cleaned_citations = [f.lower() for f in found_citations]
                claims.append((sentence, cleaned_citations))

        elif isinstance(node, dict):
            for k, v in node.items():
                if k in ("hashtags", "fact_ids_used", "layout_style", "colour_theme", "order", "slide_no", "scene_no"):
                    continue
                _traverse(v)

        elif isinstance(node, list):
            for item in node:
                _traverse(item)

    _traverse(content)
    return claims


def verify_output_facts(
    content: Dict[str, Any],
    valid_fact_ids: Set[str],
    fact_statements_map: Optional[Dict[str, str]] = None,
    domain_key: str = "general",
) -> Tuple[float, List[str], List[Dict[str, Any]]]:
    """
    Verify claims in generated output against valid Fact Registry IDs and domain pack constraints.
    Grounding is evaluated cleanly based on declared fact_ids_used, non-invention statements,
    semantic/statement alignment, and domain-specific rules (CVE, Tx Hash, Addresses).

    Returns:
        (confidence_score: float, fact_ids_used: List[str], unverified_claims: List[Dict])
    """
    from ai_services.domains.domain_router import domain_router

    valid_set = {f.lower() for f in valid_fact_ids}
    extracted_claims = extract_claims_and_citations(content)

    # Collect all declared or embedded fact IDs
    declared_fact_ids = [f.lower() for f in content.get("fact_ids_used", [])]
    all_cited_ids = set(declared_fact_ids)

    unverified_claims: List[Dict[str, Any]] = []
    verified_claim_count = 0
    total_claims = len(extracted_claims)

    # 1. Domain-specific constraint validation (Cybersecurity & Blockchain)
    if fact_statements_map:
        source_text = " ".join(fact_statements_map.values())
        if domain_key == "general":
            detected_key, _, score = domain_router.detect_domain(source_text)
            if score >= 0.3:
                domain_key = detected_key

        domain_pack = domain_router.get_domain(domain_key)
        source_domain_entities = domain_pack.extract_domain_entities(source_text)
        domain_issues = domain_pack.validate_domain_constraints(source_domain_entities, content)

        for issue in domain_issues:
            unverified_claims.append({
                "claim": f"Domain validation check ({issue['domain']})",
                "reason": issue["description"],
                "cited_fact_ids": [],
                "severity": issue.get("severity", "high"),
                "issue_type": issue.get("issue_type", "domain_violation"),
            })

    # 2. Check if any declared fact_ids_used are invalid
    invalid_declared = [fid for fid in declared_fact_ids if fid not in valid_set]
    if invalid_declared:
        for fid in invalid_declared:
            unverified_claims.append({
                "claim": f"Declared fact_ids_used entry: {fid}",
                "reason": f"Fact ID '{fid}' does not exist in document Fact Registry",
                "cited_fact_ids": [fid],
            })

    # 3. Evaluate each extracted text claim
    for sentence, inline_citations in extracted_claims:
        all_cited_ids.update(inline_citations)

        # Check explicit non-invention phrases
        sentence_lower = sentence.lower()
        if "not specified" in sentence_lower or "not provided" in sentence_lower or "no information" in sentence_lower:
            verified_claim_count += 1
            continue

        # If inline citations are present, verify them
        if inline_citations:
            invalid_citations = [c for c in inline_citations if c not in valid_set]
            if invalid_citations:
                unverified_claims.append({
                    "claim": sentence,
                    "reason": f"Cited fact ID(s) {invalid_citations} do not exist in Fact Registry",
                    "cited_fact_ids": inline_citations,
                })
            else:
                verified_claim_count += 1
            continue

        # If no inline citation, check against declared_fact_ids & document fact statements
        if declared_fact_ids and any(fid in valid_set for fid in declared_fact_ids):
            verified_claim_count += 1
        else:
            # Check if sentence aligns with any valid fact statement
            matched_fact = False
            if fact_statements_map:
                for fid, stmt in fact_statements_map.items():
                    if stmt.lower() in sentence_lower or sentence_lower[:40] in stmt.lower():
                        matched_fact = True
                        all_cited_ids.add(fid.lower())
                        break

            if matched_fact:
                verified_claim_count += 1
            else:
                unverified_claims.append({
                    "claim": sentence,
                    "reason": "Claim cannot be linked to any active Fact Registry entry",
                    "cited_fact_ids": [],
                })

    # Deduct confidence score if domain critical issues exist
    critical_domain_issues = sum(1 for c in unverified_claims if c.get("severity") == "critical")

    if total_claims == 0:
        confidence_score = 1.0 if critical_domain_issues == 0 else 0.0
    else:
        base_score = round(verified_claim_count / max(1, total_claims), 2)
        confidence_score = max(0.0, base_score - (critical_domain_issues * 0.4))

    return round(confidence_score, 2), sorted(list(all_cited_ids)), unverified_claims



def check_cross_output_consistency(
    outputs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compare facts, dates, and numerical metrics across all generated outputs in a job.
    Detects if two outputs cite the same fact ID or discuss the same metric/date with conflicting values.
    """
    inconsistencies: List[Dict[str, Any]] = []

    # Map: fact_id -> list of (output_type, sentence, dates, numbers)
    fact_usages: Dict[str, List[Dict[str, Any]]] = {}
    numbers_map: Dict[str, List[Tuple[str, str]]] = {}

    for out in outputs:
        out_type = out.get("output_type", "unknown")
        content = out.get("content", {})
        claims = extract_claims_and_citations(content)
        declared_fids = [f.lower() for f in content.get("fact_ids_used", [])]

        for sentence, inline_citations in claims:
            dates = DATE_REGEX.findall(sentence)
            numbers = NUMBER_REGEX.findall(sentence)

            combined_fids = set(inline_citations) | set(declared_fids)
            for fid in combined_fids:
                fid_lower = fid.lower()
                if fid_lower not in fact_usages:
                    fact_usages[fid_lower] = []
                fact_usages[fid_lower].append({
                    "output_type": out_type,
                    "sentence": sentence,
                    "dates": set(d.lower() for d in dates),
                    "numbers": set(numbers),
                })

            for n in numbers:
                n_clean = n.strip()
                if len(n_clean) >= 2 or (n_clean.isdigit() and int(n_clean) > 10):
                    if n_clean not in numbers_map:
                        numbers_map[n_clean] = []
                    numbers_map[n_clean].append((out_type, sentence))

    # 1. Compare usages of the same fact_id across different output formats
    for fid, usages in fact_usages.items():
        if len(usages) < 2:
            continue
        for i in range(len(usages)):
            for j in range(i + 1, len(usages)):
                u1 = usages[i]
                u2 = usages[j]
                if u1["output_type"] == u2["output_type"]:
                    continue

                if u1["dates"] and u2["dates"] and u1["dates"] != u2["dates"]:
                    inconsistencies.append({
                        "fact_id": fid,
                        "type": "date_mismatch",
                        "output_1": u1["output_type"],
                        "claim_1": u1["sentence"],
                        "output_2": u2["output_type"],
                        "claim_2": u2["sentence"],
                        "details": f"Date mismatch: '{list(u1['dates'])}' vs '{list(u2['dates'])}'",
                    })

                elif u1["numbers"] and u2["numbers"] and u1["numbers"] != u2["numbers"]:
                    inconsistencies.append({
                        "fact_id": fid,
                        "type": "number_mismatch",
                        "output_1": u1["output_type"],
                        "claim_1": u1["sentence"],
                        "output_2": u2["output_type"],
                        "claim_2": u2["sentence"],
                        "details": f"Metric mismatch: '{list(u1['numbers'])}' vs '{list(u2['numbers'])}'",
                    })

    # 2. Cross-check scale mismatches (e.g., 500 vs 5000)
    all_numbers = list(numbers_map.keys())
    for i in range(len(all_numbers)):
        for j in range(i + 1, len(all_numbers)):
            n1, n2 = all_numbers[i], all_numbers[j]
            if n1 != n2 and (n1 + "0" == n2 or n2 + "0" == n1):
                u1 = numbers_map[n1][0]
                u2 = numbers_map[n2][0]
                if u1[0] != u2[0]:
                    inconsistencies.append({
                        "type": "number_mismatch",
                        "output_1": u1[0],
                        "claim_1": u1[1],
                        "output_2": u2[0],
                        "claim_2": u2[1],
                        "details": f"Cross-output metric conflict: '{n1}' reported in {u1[0]} vs '{n2}' reported in {u2[0]}",
                    })

    return inconsistencies


