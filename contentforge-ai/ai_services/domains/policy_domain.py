import re
from typing import Any, Dict, List
from ai_services.domains.base_domain import BaseDomain

POLICY_KEYWORDS = {
    "regulation", "compliance", "policy", "statute", "governance", "executive order",
    "directive", "legislation", "regulatory", "audit", "mandate"
}


class PolicyDomain(BaseDomain):
    @property
    def domain_key(self) -> str:
        return "policy"

    @property
    def domain_name(self) -> str:
        return "Policy & Governance Pack"

    def detect_affinity(self, text: str) -> float:
        text_lower = text.lower()
        keyword_matches = sum(1 for kw in POLICY_KEYWORDS if kw in text_lower)
        score = min(1.0, keyword_matches * 0.20)
        return round(score, 2)

    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        return {"policy_terms": [kw for kw in POLICY_KEYWORDS if kw in text.lower()]}

    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return []
