from typing import Dict, List, Tuple
from ai_services.domains.base_domain import BaseDomain
from ai_services.domains.cybersecurity_domain import CybersecurityDomain
from ai_services.domains.blockchain_domain import BlockchainDomain
from ai_services.domains.general_domain import GeneralDomain


class DomainRouter:
    """
    Domain Router that evaluates input documents and selects the appropriate domain pack.
    """

    def __init__(self):
        self.domains: Dict[str, BaseDomain] = {
            "cybersecurity": CybersecurityDomain(),
            "blockchain": BlockchainDomain(),
            "general": GeneralDomain(),
        }

    def detect_domain(self, text: str) -> Tuple[str, BaseDomain, float]:
        """
        Calculates domain affinity scores and returns (domain_key, domain_instance, score).
        """
        scores: Dict[str, float] = {}
        for key in ["cybersecurity", "blockchain"]:
            scores[key] = self.domains[key].detect_affinity(text)

        best_key = "general"
        best_score = 0.0

        for key, score in scores.items():
            if score > best_score and score >= 0.3:
                best_score = score
                best_key = key

        return best_key, self.domains[best_key], best_score

    def get_domain(self, domain_key: str) -> BaseDomain:
        return self.domains.get(domain_key, self.domains["general"])


domain_router = DomainRouter()
