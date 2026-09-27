import re
from typing import Any, Dict, List, Set
from ai_services.domains.base_domain import BaseDomain

CVE_REGEX = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
CWE_REGEX = re.compile(r"\bCWE-\d{1,5}\b", re.IGNORECASE)
CVSS_REGEX = re.compile(r"\bCVSS(?::v\d(?:\.\d)?)?/(?:AV:[NALP]/AC:[LMH]|CVSS:\d\.\d/[^\s]+)\b", re.IGNORECASE)
IP_REGEX = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
HASH_SHA256_REGEX = re.compile(r"\b[a-fA-F0-9]{64}\b")
HASH_MD5_REGEX = re.compile(r"\b[a-fA-F0-9]{32}\b")
ATTACK_TECHNIQUE_REGEX = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")

CYBER_KEYWORDS = {
    "vulnerability", "cve", "cwe", "cvss", "exploit", "zero-day", "rce", "malware",
    "ransomware", "threat actor", "ioc", "payload", "mitigation", "patch", "denial of service",
    "remote code execution", "privilege escalation", "exfiltration", "phishing", "c2", "command and control"
}


class CybersecurityDomain(BaseDomain):
    @property
    def domain_key(self) -> str:
        return "cybersecurity"

    @property
    def domain_name(self) -> str:
        return "Cybersecurity Intelligence Pack"

    def detect_affinity(self, text: str) -> float:
        text_lower = text.lower()
        keyword_matches = sum(1 for kw in CYBER_KEYWORDS if kw in text_lower)
        cve_matches = len(CVE_REGEX.findall(text))
        ip_matches = len(IP_REGEX.findall(text))
        
        score = min(1.0, (keyword_matches * 0.15) + (cve_matches * 0.35) + (ip_matches * 0.2))
        return round(score, 2)

    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        cves = list(set(c.upper() for c in CVE_REGEX.findall(text)))
        cwes = list(set(c.upper() for c in CWE_REGEX.findall(text)))
        ips = list(set(IP_REGEX.findall(text)))
        sha256s = list(set(h.lower() for h in HASH_SHA256_REGEX.findall(text)))
        md5s = list(set(h.lower() for h in HASH_MD5_REGEX.findall(text)))
        attack_techs = list(set(a.upper() for a in ATTACK_TECHNIQUE_REGEX.findall(text)))

        return {
            "cves": cves,
            "cwes": cwes,
            "ips": ips,
            "sha256_hashes": sha256s,
            "md5_hashes": md5s,
            "attack_techniques": attack_techs,
        }

    def validate_domain_constraints(
        self,
        source_entities: Dict[str, List[str]],
        generated_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        gen_str = str(generated_content)
        gen_entities = self.extract_domain_entities(gen_str)

        # 1. Validate CVEs: Any CVE in generated output MUST exist in source
        source_cves = set(source_entities.get("cves", []))
        for gen_cve in gen_entities.get("cves", []):
            if gen_cve not in source_cves:
                issues.append({
                    "domain": self.domain_key,
                    "issue_type": "cve_mismatch_hallucination",
                    "severity": "critical",
                    "description": f"Generated output contains ungrounded CVE identifier: '{gen_cve}'. Source CVEs: {list(source_cves)}",
                })

        # 2. Validate IP addresses / IOCs
        source_ips = set(source_entities.get("ips", []))
        for gen_ip in gen_entities.get("ips", []):
            if gen_ip not in source_ips:
                issues.append({
                    "domain": self.domain_key,
                    "issue_type": "ioc_ip_mismatch",
                    "severity": "high",
                    "description": f"Generated output contains IP IOC '{gen_ip}' not present in source evidence.",
                })

        # 3. Validate hashes
        source_hashes = set(source_entities.get("sha256_hashes", [])) | set(source_entities.get("md5_hashes", []))
        gen_hashes = set(gen_entities.get("sha256_hashes", [])) | set(gen_entities.get("md5_hashes", []))
        for gen_hash in gen_hashes:
            if gen_hash not in source_hashes:
                issues.append({
                    "domain": self.domain_key,
                    "issue_type": "hash_ioc_mismatch",
                    "severity": "critical",
                    "description": f"Generated cryptographic hash '{gen_hash}' does not match any source IOC hash.",
                })

        return issues
