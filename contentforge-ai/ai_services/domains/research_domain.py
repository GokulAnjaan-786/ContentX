import re
from typing import Any, Dict, List
from ai_services.domains.base_domain import BaseDomain

RESEARCH_KEYWORDS = {
    "machine learning", "deep learning", "nlp", "natural language processing",
    "sentiment analysis", "text classification", "dataset", "neural network",
    "model", "accuracy", "precision", "recall", "f1-score", "data science",
    "algorithm", "experiment", "evaluation", "capstone", "research paper"
}


class ResearchDomain(BaseDomain):
    @property
    def domain_key(self) -> str:
        return "research"

    @property
    def domain_name(self) -> str:
        return "Research & Data Science Pack"

    def detect_affinity(self, text: str) -> float:
        text_lower = text.lower()
        keyword_matches = sum(1 for kw in RESEARCH_KEYWORDS if kw in text_lower)
        score = min(1.0, keyword_matches * 0.20)
        return round(score, 2)

    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        text_lower = text.lower()
        models = [kw for kw in ["nlp", "bert", "gpt", "transformer", "sentiment analysis", "text classification", "machine learning"] if kw in text_lower]
        return {
            "research_topics": models,
        }

    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        gen_str = str(generated_content).lower()
        
        # Check if output falsely introduces cybersecurity terms when source is research
        cyber_terms = ["cve-", "operational advisory", "threat actor", "ioc", "remediation guidance"]
        for term in cyber_terms:
            if term in gen_str and not any(term in str(source_entities).lower() for term in cyber_terms):
                issues.append({
                    "domain": self.domain_key,
                    "issue_type": "domain_contamination_cybersecurity",
                    "severity": "high",
                    "description": f"Generated output falsely introduces cybersecurity phrase '{term}' into research/data science context.",
                })
        return issues
