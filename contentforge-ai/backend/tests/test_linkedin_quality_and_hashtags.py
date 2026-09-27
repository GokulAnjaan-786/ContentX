import pytest
import asyncio
from app.models.fact_registry import FactRegistry
from ai_services.orchestrator.context_builder import build_generator_context
from ai_services.generators.linkedin_generator import generate_linkedin_post
from ai_services.generators.hashtag_intelligence import generate_hashtag_intelligence
from ai_services.domains.domain_router import domain_router
from ai_services.validation.fact_checker import verify_output_facts


@pytest.mark.asyncio
async def test_1_normal_ml_document_no_cyber_contamination():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="Predict drug sentiment from patient comments using machine learning and NLP text classification.",
            importance="high",
            fact_type="finding",
            certainty_status="confirmed"
        ),
        FactRegistry(
            fact_id_string="f2",
            fact_statement="Evaluated classification model performance on 10,000 patient reviews with 92% accuracy.",
            importance="high",
            fact_type="statistic",
            certainty_status="confirmed",
            numbers=["10000", "92%"]
        )
    ]

    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})

    body_text = (post["hook"] + " " + post["body"]).lower()
    assert "cybersecurity" not in body_text
    assert "operational advisory" not in body_text
    assert "remediation guidance" not in body_text
    assert any(tag in ["#MachineLearning", "#NLP", "#SentimentAnalysis", "#DataScience"] for tag in post["hashtags"])


@pytest.mark.asyncio
async def test_2_cybersecurity_document():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="CVE-2024-1234 represents an unauthenticated RCE vulnerability in API Gateway.",
            importance="high",
            fact_type="incident_finding",
            certainty_status="confirmed"
        ),
        FactRegistry(
            fact_id_string="f2",
            fact_statement="Security analysts recommend applying patch version 2.4.1 immediately.",
            importance="high",
            fact_type="action_item",
            certainty_status="confirmed"
        )
    ]

    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})

    assert any(tag in ["#CyberSecurity", "#ThreatIntel", "#IncidentResponse", "#InfoSec"] for tag in post["hashtags"])
    assert "#MachineLearning" not in post["hashtags"]
    assert "#Blockchain" not in post["hashtags"]


@pytest.mark.asyncio
async def test_3_blockchain_document():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="Smart contract audit identified reentrancy risk in decentralized vault module.",
            importance="high",
            fact_type="finding",
            certainty_status="confirmed"
        )
    ]

    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})

    assert any(tag in ["#Blockchain", "#Web3", "#SmartContracts"] for tag in post["hashtags"])
    assert "#CyberSecurity" not in post["hashtags"]


@pytest.mark.asyncio
async def test_4_extraction_noise_filtering():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="page 2 of 11 project overview total marks: 100 submission: code + presentation predictions.csv",
            importance="metadata",
            fact_type="document_metadata",
            certainty_status="confirmed"
        ),
        FactRegistry(
            fact_id_string="f2",
            fact_statement="Machine learning classification model achieved 88% F1-score on test dataset.",
            importance="high",
            fact_type="finding",
            certainty_status="confirmed"
        )
    ]

    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    assert "page 2 of 11" not in formatted_facts
    assert "predictions.csv" not in formatted_facts
    assert "total marks:" not in formatted_facts

    post = await generate_linkedin_post(formatted_facts, raw_facts, {})
    assert "page 2 of 11" not in str(post)
    assert "predictions.csv" not in str(post)


@pytest.mark.asyncio
async def test_5_certainty_preservation():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="The security incident may affect 500 systems.",
            importance="high",
            fact_type="incident_finding",
            certainty_status="uncertain"
        )
    ]

    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})
    post_str = (post.get("hook", "") + " " + post.get("body", "")).lower()

    assert "may affect" in post_str or "could affect" in post_str or "unconfirmed" in post_str or "potential" in post_str


@pytest.mark.asyncio
async def test_6_number_preservation():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="The telemetric survey verified 500 systems were evaluated.",
            importance="high",
            fact_type="statistic",
            certainty_status="confirmed",
            numbers=["500"]
        )
    ]

    formatted_facts, raw_facts = build_generator_context(facts, "linkedin", {})
    post = await generate_linkedin_post(formatted_facts, raw_facts, {})
    post_str = str(post)

    assert "500" in post_str
    assert "5000" not in post_str


def test_7_hashtag_intelligence_count_and_relevance():
    raw_facts = [
        {"fact_statement": "Predicting drug sentiment using NLP and machine learning algorithms."}
    ]

    res = generate_hashtag_intelligence(raw_facts=raw_facts, domain_key="research")
    tags = res["hashtags"]

    assert 3 <= len(tags) <= 6
    assert all(t.startswith("#") for t in tags)
    assert "#SentimentAnalysis" in tags or "#NLP" in tags or "#MachineLearning" in tags


def test_8_trend_data_unavailable_fallback():
    raw_facts = [{"fact_statement": "Quarterly enterprise software revenue increased by 15%."}]
    res = generate_hashtag_intelligence(raw_facts=raw_facts, domain_key="business", trend_data_available=False)

    assert res["is_trend_aware"] is False
    for suggestion in res["suggestions"]:
        assert suggestion["trend_status"] == "unavailable"
        assert "Trending" not in suggestion["label"] or "Relevant" in suggestion["label"]


@pytest.mark.asyncio
async def test_9_same_source_multiple_audiences_facts_consistency():
    facts = [
        FactRegistry(
            fact_id_string="f1",
            fact_statement="On 2026-03-15, patch version 4.2.0 was deployed to 120 nodes.",
            importance="high",
            fact_type="action_item",
            certainty_status="confirmed",
            dates=["2026-03-15"],
            numbers=["4.2.0", "120"]
        )
    ]

    fmt_tech, raw_tech = build_generator_context(facts, "linkedin", {}, audience="technical")
    fmt_exec, raw_exec = build_generator_context(facts, "linkedin", {}, audience="executive")

    post_tech = await generate_linkedin_post(fmt_tech, raw_tech, {})
    post_exec = await generate_linkedin_post(fmt_exec, raw_exec, {})

    str_tech = str(post_tech)
    str_exec = str(post_exec)

    assert "120" in str_tech and "120" in str_exec
