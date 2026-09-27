import re
from typing import Any, Dict, List, Optional


KNOWN_DOMAIN_HASHTAGS = {
    "research": ["#MachineLearning", "#NLP", "#SentimentAnalysis", "#DataScience", "#ArtificialIntelligence", "#TextClassification"],
    "cybersecurity": ["#CyberSecurity", "#ThreatIntel", "#IncidentResponse", "#InfoSec", "#CyberSecurityAwareness", "#TechLeadership"],
    "blockchain": ["#Blockchain", "#Web3", "#SmartContracts", "#CryptoSecurity", "#DeFi", "#TechInnovation"],
    "business": ["#BusinessStrategy", "#Leadership", "#EnterpriseTech", "#FinancialGrowth", "#ExecutiveInsights", "#Innovation"],
    "education": ["#EdTech", "#HigherEducation", "#DataScience", "#AcademicResearch", "#LearningAndDevelopment"],
    "policy": ["#RegulatoryCompliance", "#TechPolicy", "#Governance", "#DataPrivacy", "#LegalTech"],
    "general": ["#TechInnovation", "#ProfessionalInsights", "#Leadership", "#DigitalTransformation"]
}


def clean_hashtag(tag: str) -> str:
    """Format hashtag into valid #CamelCase without spaces or illegal characters."""
    if not tag:
        return ""
    tag = tag.strip()
    if not tag.startswith("#"):
        tag = f"#{tag}"
    # Remove spaces and non-alphanumeric chars except hashtag symbol
    cleaned = re.sub(r"[^\w#]", "", tag)
    return cleaned


def generate_hashtag_intelligence(
    raw_facts: List[Dict[str, Any]],
    domain_key: str = "general",
    topics: Optional[List[str]] = None,
    summary: str = "",
    trend_data_available: bool = False,
    trend_source_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate 3-6 highly relevant LinkedIn hashtags based on source facts, topics, and domain.
    Operates independently from core LLM generation.
    Gracefully handles real-time trend availability vs evergreen fallback.
    """
    combined_text = (summary + " " + " ".join(f.get("fact_statement", "") for f in raw_facts)).lower()
    selected_tags: List[str] = []
    suggestions: List[Dict[str, Any]] = []

    # 1. Topic-Based Hashtag Selection
    topic_candidates = []
    if "sentiment" in combined_text or "drug" in combined_text:
        topic_candidates.extend(["#SentimentAnalysis", "#NLP", "#MachineLearning", "#TextClassification", "#DataScience"])
    elif "nlp" in combined_text or "text classification" in combined_text:
        topic_candidates.extend(["#NLP", "#TextClassification", "#MachineLearning", "#ArtificialIntelligence"])
    elif "cve" in combined_text or "vulnerability" in combined_text or "malware" in combined_text:
        topic_candidates.extend(["#CyberSecurity", "#ThreatIntel", "#IncidentResponse", "#InfoSec"])
    elif "blockchain" in combined_text or "smart contract" in combined_text:
        topic_candidates.extend(["#Blockchain", "#Web3", "#SmartContracts"])
    elif "revenue" in combined_text or "profit" in combined_text or "quarterly" in combined_text:
        topic_candidates.extend(["#BusinessStrategy", "#FinancialGrowth", "#EnterpriseTech"])

    # 2. Add Domain Defaults if needed
    domain_defaults = KNOWN_DOMAIN_HASHTAGS.get(domain_key, KNOWN_DOMAIN_HASHTAGS["general"])
    for tag in topic_candidates + domain_defaults:
        c_tag = clean_hashtag(tag)
        if c_tag and c_tag not in selected_tags:
            selected_tags.append(c_tag)
        if len(selected_tags) >= 6:
            break

    # Target: 3 to 6 hashtags
    if len(selected_tags) < 3:
        for tag in KNOWN_DOMAIN_HASHTAGS["general"]:
            c_tag = clean_hashtag(tag)
            if c_tag not in selected_tags:
                selected_tags.append(c_tag)
            if len(selected_tags) >= 3:
                break

    final_hashtags = selected_tags[:5]  # Optimal LinkedIn range 3-5

    # Build trend metadata suggestions
    for idx, tag in enumerate(final_hashtags):
        is_primary = idx == 0
        tag_type = "primary_topic" if is_primary else ("domain_industry" if idx == 1 else "supporting_topic")
        
        status = "supported" if trend_data_available else "unavailable"
        label = f"Trending Topic ({trend_source_name})" if trend_data_available else "Relevant Topic Hashtag"

        suggestions.append({
            "tag": tag,
            "type": tag_type,
            "trend_status": status,
            "label": label,
        })

    return {
        "hashtags": final_hashtags,
        "suggestions": suggestions,
        "is_trend_aware": trend_data_available,
    }
