from typing import Any, Dict, List
from ai_services.domains.base_domain import BaseDomain


class GeneralDomain(BaseDomain):
    @property
    def domain_key(self) -> str:
        return "general"

    @property
    def domain_name(self) -> str:
        return "General Information Intelligence Pack"

    def detect_affinity(self, text: str) -> float:
        return 0.1  # Default fallback score

    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        return {}

    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return []
