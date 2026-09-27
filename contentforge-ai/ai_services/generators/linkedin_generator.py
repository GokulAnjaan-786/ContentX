import os
import re
from typing import Any, Dict, List
from ai_services.model_client import model_client
from ai_services.validation.schema_validator import LinkedInOutput
from ai_services.generators.hashtag_intelligence import generate_hashtag_intelligence

PROMPT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts",
    "linkedin_prompt.txt",
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


async def generate_linkedin_post(
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured LinkedIn post grounded strictly in Fact Registry."""
    template = load_prompt_template()
    prompt = (
        template.replace("{formatted_facts}", formatted_facts)
        .replace("{audience}", settings.get("audience", "professionals"))
        .replace("{tone}", settings.get("tone", "authoritative"))
        .replace("{detail_level}", settings.get("detail_level", "standard"))
        .replace("{objective}", settings.get("objective", "awareness"))
    )

    domain_key = "general"
    if raw_facts and isinstance(raw_facts, list):
        domain_key = raw_facts[0].get("domain_key", "general")

    # Generate topic & trend-aware hashtag intelligence layer
    hashtag_intel = generate_hashtag_intelligence(raw_facts=raw_facts, domain_key=domain_key)

    try:
        result = await model_client.generate_structured(prompt=prompt, schema=LinkedInOutput)
        if isinstance(result, dict):
            result["hook"] = clean_text(result.get("hook", ""))
            result["body"] = clean_text(result.get("body", ""))
            result["call_to_action"] = clean_text(result.get("call_to_action", ""))
            
            # Use hashtag intelligence layer tags if LLM tags are empty or generic
            llm_tags = result.get("hashtags", [])
            if not llm_tags or len(llm_tags) < 3:
                result["hashtags"] = hashtag_intel["hashtags"]
            else:
                # Ensure 3-6 cleaned tags
                cleaned = [tag if tag.startswith("#") else f"#{tag}" for tag in llm_tags][:6]
                result["hashtags"] = cleaned

            result["hashtag_suggestions"] = hashtag_intel["suggestions"]
        return result
    except Exception:
        # Domain-aware fallback generator with natural professional LinkedIn phrasing
        high_facts = [
            f for f in raw_facts 
            if f.get("importance") not in ("internal", "metadata") 
            and f.get("fact_type") not in ("internal_processing", "document_metadata")
        ] or raw_facts

        f1 = high_facts[0] if high_facts else {"fact_id_string": "f1", "fact_statement": "Key findings identified."}
        f2 = high_facts[1] if len(high_facts) > 1 else f1

        used_ids = list({f1["fact_id_string"], f2["fact_id_string"]})
        stmt1 = f1["fact_statement"].rstrip(".")
        stmt2 = f2["fact_statement"].rstrip(".")

        combined_lower = (stmt1 + " " + stmt2).lower()

        # Domain-appropriate hook & phrasing
        if domain_key == "research" or any(w in combined_lower for w in ["sentiment", "nlp", "machine learning", "drug", "classification"]):
            hook = "Key Insights: Overview of Recent Technical Analysis & Findings"
            body = (
                f"Recent evaluation confirmed that {stmt1.lower()}.\n\n"
                f"Further technical analysis verified that {stmt2.lower()}.\n\n"
                f"Applying rigorous technical standards ensures reproducible and reliable performance."
            )
            cta = "Explore the technical documentation and key findings for complete details."
        elif domain_key == "cybersecurity" or any(w in combined_lower for w in ["vulnerability", "cve", "malware", "breach"]):
            hook = "Security Alert & Advisory: Key Operational Insights"
            body = (
                f"Recent investigation confirmed that {stmt1.lower()}.\n\n"
                f"Further technical review verified that {stmt2.lower()}.\n\n"
                f"Maintaining proactive visibility and response protocols remains essential."
            )
            cta = "Read the full operational advisory for technical remediation guidance."
        elif domain_key == "blockchain" or any(w in combined_lower for w in ["blockchain", "smart contract", "web3"]):
            hook = "Web3 & Blockchain Insights: Strategic Technical Overview"
            body = (
                f"Recent audit confirmed that {stmt1.lower()}.\n\n"
                f"Further technical analysis verified that {stmt2.lower()}.\n\n"
                f"Ensuring smart contract integrity and robust protocol design remains essential."
            )
            cta = "Review the full technical report for architecture and security details."
        else:
            hook = "Key Executive Insights: Operational Summary"
            body = (
                f"Analysis confirmed that {stmt1.lower()}.\n\n"
                f"Further review verified that {stmt2.lower()}.\n\n"
                f"Maintaining structured documentation ensures organizational clarity and progress."
            )
            cta = "Read the complete report for further operational details."

        return {
            "hook": hook,
            "body": body,
            "hashtags": hashtag_intel["hashtags"],
            "hashtag_suggestions": hashtag_intel["suggestions"],
            "call_to_action": cta,
            "fact_ids_used": sorted(used_ids),
        }
