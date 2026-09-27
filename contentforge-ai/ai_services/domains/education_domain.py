import re
from typing import Any, Dict, List
from ai_services.domains.base_domain import BaseDomain

EDUCATION_KEYWORDS = {
    "capstone", "student", "curriculum", "assignment", "submission", "course",
    "university", "academic", "grading", "syllabus", "lecture", "student comments"
}


class EducationDomain(BaseDomain):
    @property
    def domain_key(self) -> str:
        return "education"

    @property
    def domain_name(self) -> str:
        return "Education & Academic Pack"

    def detect_affinity(self, text: str) -> float:
        text_lower = text.lower()
        keyword_matches = sum(1 for kw in EDUCATION_KEYWORDS if kw in text_lower)
        score = min(1.0, keyword_matches * 0.20)
        return round(score, 2)

    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        return {"education_terms": [kw for kw in EDUCATION_KEYWORDS if kw in text.lower()]}

    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return []
