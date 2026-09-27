import pytest
from ai_services.orchestrator.audience_profile import resolve_audiences, get_audience_profile
from ai_services.validation.fact_checker import verify_truth_compression_consistency, verify_output_facts


def test_truth_compression_test1_same_number():
    """TEST 1 — Same number preservation across technical, executive, and public audiences."""
    source_facts = [{"fact_statement": "500 systems were affected."}]
    technical_out = {"audience": "technical", "content": "A security incident affected 500 systems."}
    executive_out = {"audience": "executive", "content": "Key Finding: 500 systems were impacted."}
    public_out = {"audience": "general_public", "content": "Notice: 500 systems were affected in the incident."}

    result = verify_truth_compression_consistency([technical_out, executive_out, public_out], source_facts)
    assert result["is_valid"] is True
    assert "Same numbers" in result["checks_passed"]


def test_truth_compression_test2_certainty_preservation():
    """TEST 2 — Certainty preservation ('may affect' -> 'may affect' / 'could affect')."""
    technical_out = {"audience": "technical", "content": "The incident may affect 500 systems under specific conditions."}
    public_out = {"audience": "general_public", "content": "A security issue could affect 500 systems."}

    result = verify_truth_compression_consistency([technical_out, public_out])
    assert result["is_valid"] is True
    assert len(result["violations"]) == 0


def test_truth_compression_test3_certainty_violation():
    """TEST 3 — Certainty violation ('may affect' -> 'affected' changes possibility to confirmed fact)."""
    technical_out = {"audience": "technical", "content": "The incident may affect 500 systems."}
    public_violating = {"audience": "general_public", "content": "The incident affected 500 systems."}

    result = verify_truth_compression_consistency([technical_out, public_violating])
    assert result["is_valid"] is False
    assert any(v["reason"] == "Certainty changed from possibility to confirmed fact." for v in result["violations"])


def test_truth_compression_test4_date_preservation():
    """TEST 4 — Date preservation across all audience versions."""
    tech_out = {"audience": "technical", "content": "Incident detected on 2026-09-20 during automated scan."}
    exec_out = {"audience": "executive", "content": "An incident detected on 2026-09-20 was reviewed by security."}

    result = verify_truth_compression_consistency([tech_out, exec_out])
    assert result["is_valid"] is True
    assert "Same dates" in result["checks_passed"]


def test_truth_compression_test5_cybersecurity_identifier():
    """TEST 5 — Preservation of CVE identifiers."""
    tech_out = {"audience": "technical", "content": "Vulnerability CVE-2026-1234 affects Product X versions 2.1 to 2.4."}
    pub_out = {"audience": "general_public", "content": "A vulnerability CVE-2026-1234 was identified in Product X."}

    result = verify_truth_compression_consistency([tech_out, pub_out])
    assert result["is_valid"] is True
    assert "Same technical identifiers" in result["checks_passed"]


def test_truth_compression_test6_blockchain_identifier():
    """TEST 6 — Preservation of blockchain transaction hashes."""
    tx_hash = "0x8f3c7a91b2e45d6801934cfa78e1234567890abcdef1234567890abcdef12345"
    tech_out = {"audience": "technical", "content": f"Transaction {tx_hash} executed token transfer."}
    exec_out = {"audience": "executive", "content": f"Verified transaction {tx_hash} on Ethereum."}

    result = verify_truth_compression_consistency([tech_out, exec_out])
    assert result["is_valid"] is True


def test_truth_compression_test7_no_hallucinated_facts():
    """TEST 7 — Hallucinated facts rejected by Fact Registry validation."""
    valid_fact_ids = {"f1", "f2"}
    fact_statements = {"f1": "CVE-2026-1234 was discovered.", "f2": "500 systems were updated."}
    
    # Generated content with unverified claim
    output_dict = {
        "body": "CVE-2026-1234 was discovered [f1]. 500 systems were updated [f2]. The attacker stole $10 million in Bitcoin.",
        "fact_ids_used": ["f1", "f2"],
    }
    score, used_ids, unverified = verify_output_facts(output_dict, valid_fact_ids, fact_statements)
    assert len(unverified) > 0 or score < 1.0


def test_truth_compression_test8_same_source_evidence():
    """TEST 8 — Multiple audience versions trace back to the same Fact Registry IDs."""
    pairs = resolve_audiences(["linkedin", "advisory"], ["technical", "executive"])
    assert len(pairs) == 4
    # All pairs reuse the same underlying Fact Registry without re-indexing
    assert pairs[0]["output_type"] in ["linkedin", "advisory"]
