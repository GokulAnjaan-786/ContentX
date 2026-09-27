from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class BaseDomain(ABC):
    """
    Abstract Base Class for Domain Intelligence Packs in ContentX.
    """

    @property
    @abstractmethod
    def domain_key(self) -> str:
        pass

    @property
    @abstractmethod
    def domain_name(self) -> str:
        pass

    @abstractmethod
    def detect_affinity(self) -> float:
        """
        Calculate affinity score (0.0 to 1.0) for a given text or set of facts.
        """
        pass

    @abstractmethod
    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract domain-specific structured entities (e.g., CVEs, IOCs, Tx Hashes, Addresses).
        """
        pass

    @abstractmethod
    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Validate generated output against source domain entities.
        Returns a list of domain validation issues if mismatches or hallucinations are detected.
        """
        pass
