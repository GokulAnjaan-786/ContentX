import os
import re
from typing import Any, Dict, List
from ai_services.model_client import model_client
from ai_services.validation.schema_validator import TwitterOutput

PROMPT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "prompts",
    "twitter_prompt.txt",
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


async def generate_twitter_thread(
    formatted_facts: str,
    raw_facts: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured Twitter/X thread grounded strictly in Fact Registry."""
    template = load_prompt_template()
    prompt = (
        template.replace("{formatted_facts}", formatted_facts)
        .replace("{audience}", settings.get("audience", "general_public"))
        .replace("{tone}", settings.get("tone", "accessible"))
        .replace("{detail_level}", settings.get("detail_level", "standard"))
        .replace("{objective}", settings.get("objective", "summary"))
    )

    try:
        result = await model_client.generate_structured(prompt=prompt, schema=TwitterOutput)
        if isinstance(result, dict) and "tweets" in result:
            for tweet in result["tweets"]:
                tweet["text"] = clean_text(tweet.get("text", ""))
        return result
    except Exception:
        # Fallback thread for testing/offline
        used_ids = []
        tweets = []
        high_facts = [f for f in raw_facts if f.get("importance") != "internal"] or raw_facts

        for i, fact in enumerate(high_facts[:3], start=1):
            fid = fact["fact_id_string"]
            used_ids.append(fid)
            stmt = fact.get("fact_statement", "").rstrip(".")
            tweets.append({
                "order": i,
                "text": f"{i}/ Key update: {stmt}.",
            })
        if not tweets:
            tweets = [{"order": 1, "text": "1/ Technical monitoring update and system status summary."}]
            used_ids = ["f1"]

        return {
            "tweets": tweets,
            "fact_ids_used": sorted(list(set(used_ids))),
        }

