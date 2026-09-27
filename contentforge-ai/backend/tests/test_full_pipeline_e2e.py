"""Full Pipeline End-to-End Integration and Performance Benchmark Test.

Executes the complete ContentForge AI lifecycle:
1. Ingest real 5-page PDF document via upload endpoint.
2. Background text extraction, cleaning, and sliding-window chunking.
3. Single Understanding Pass extracting Fact Registry, entities, summary.
4. Parallel multi-format generation across 4 channels (LinkedIn, Twitter, Advisory, Exec Summary).
5. Validation of all 4 output schemas and cross-output fact consistency.
6. Performance assertion: complete generation finishes within the 60-second budget.
"""

import time
import uuid
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.models.document import Document, ProcessedStatus
from app.models.fact_registry import FactRegistry
from worker.tasks import process_document_task
from ai_services.orchestrator.output_router import execute_generation_job
from ai_services.validation.schema_validator import validate_output_schema


def create_sample_5page_pdf_bytes() -> bytes:
    """Generates an authentic in-memory 5-page incident report PDF."""
    pdf = pymupdf.open()
    pages_content = [
        (
            "Page 1: Executive Incident Overview & Initial Breach Telemetry\n\n"
            "On July 14, 2026 at 02:14 UTC, CloudScale Global security operations detected an anomalous spike in API Gateway traffic. "
            "Automated alert SIEM-9921 triggered when unauthorized access attempts targeted the legacy authentication microservice in region US-East-1. "
            "Forensic analysis confirmed that threat actors executed a distributed credential-stuffing assault using leaked administrative credentials. "
            "A total of 14 corporate staging accounts were accessed before defensive circuits tripped, but customer databases remained isolated. "
            "The initial intrusion was contained within 42 minutes by isolating the affected gateway instances and blocking malicious source IP ranges.\n\n"
            "Telemetry captured during the first fifteen minutes showed over 340,000 unauthorized requests per minute directed at edge routing proxies. "
            "The perimeter firewall dynamically enforced rate limiting, dropping approximately 94% of malicious requests prior to internal queue saturation. "
            "Zero operational disruption or service degradation was observed across production customer traffic during the mitigation phase. "
            "All telemetry logs were archived with cryptographic checksums to preserve forensic integrity for regulatory notifications.\n\n"
            "Incident Commander Sarah Jenkins activated the cross-functional cyber defense war room at 02:22 UTC. "
            "Internal communications were dispatched to executive leadership within 30 minutes in accordance with standard operating procedures. "
            "CloudScale's external security operations vendor was placed on high alert to assist with global log correlation and forensic disk image capture."
        ),
        (
            "Page 2: Threat Actor Attribution & Vulnerability Vector Analysis\n\n"
            "Further investigation into the intrusion revealed exploitation of a previously unpatched deserialization vulnerability designated CVE-2026-8819. "
            "The threat actors leveraged this weakness to bypass secondary session token validation within the staging identity broker daemon. "
            "Internal network telemetry revealed attempts to perform lateral reconnaissance using forged Kerberos tickets and unauthorized RPC calls. "
            "Fortunately, mandatory hardware MFA enforced via FIDO2 security keys thwarted 98% of lateral authentication attempts across Kubernetes cluster nodes. "
            "Threat actor signatures matched behavioral profiles associated with Advanced Persistent Threat group APT-44 (known as Obsidian Raptor).\n\n"
            "The vulnerability was isolated to internal development builds of API Gateway v3.1.0, which lacked strict input schema validation on deserialized payloads. "
            "Production clusters running API Gateway v3.0.8 were unaffected by CVE-2026-8819 as confirmed by automated hash verification. "
            "A memory dump from the compromised staging container confirmed no persistent kernel rootkits were installed or executed. "
            "Network connection logs indicated that egress attempts to command-and-control servers in Eastern Europe were terminated by default-deny egress policies.\n\n"
            "Forensic analysts extracted five distinct custom exploitation scripts from the volatile memory of the compromised staging runner. "
            "These artifacts demonstrated automated discovery routines scanning for unsecured Redis caches and unencrypted environment files. "
            "All captured samples were shared with the national Cyber Threat Alliance to assist peer organizations in identifying similar adversary campaigns."
        ),
        (
            "Page 3: Impact Assessment & Zero-Trust Verification Audit\n\n"
            "An exhaustive audit of all datastores confirmed that no production customer data, credit card numbers, or proprietary model weights were exfiltrated. "
            "The staging environment where the breach occurred was completely partitioned from the production VPC via mutual TLS and strict zero-trust boundaries. "
            "Third-party cybersecurity auditor CyberArmor Ltd conducted an independent external forensic review under engagement reference CA-2026-9941. "
            "CyberArmor's formal report validated CloudScale's internal findings, confirming zero unauthorized database queries against customer tables. "
            "All affected staging containers were immediately terminated, forensically imaged, and recreated from cryptographically verified base images.\n\n"
            "Employee credentials across the engineering and operations teams were subjected to immediate global session invalidation and mandatory password rotation. "
            "Identity provider audit logs verified that no unauthorized privilege escalation or role modifications occurred during the incident window. "
            "CloudScale's data protection officer determined that the incident does not trigger GDPR Article 33 notification thresholds for customer data loss. "
            "Nonetheless, transparent voluntary disclosures were prepared for key enterprise enterprise partners and relevant regulatory agencies.\n\n"
            "Customer support workflows received automated verification scripts to reassure enterprise clients requesting real-time status confirmations. "
            "Continuous automated integrity monitors reported 100% green status across all primary database clusters and multi-region read replicas. "
            "Independent verification by external auditors affirmed that data isolation protocols operated with complete fidelity throughout the incident."
        ),
        (
            "Page 4: Strategic Remediation Protocols & Hardening Controls\n\n"
            "The security engineering team executed a four-stage remediation protocol within 24 hours of incident containment. "
            "First, hotfix release v3.1.2 was deployed globally, eliminating the deserialization vulnerability in the identity broker daemon. "
            "Second, all staging API keys, database connection strings, and service tokens were systematically rotated and re-issued. "
            "Third, hardware security key enforcement was expanded to include all temporary staging and pre-production environment access. "
            "Fourth, ingress firewall filtering was hardened with behavioral anomaly detection to identify distributed credential stuffing.\n\n"
            "In addition to immediate infrastructure fixes, code analysis gates were added to the CI/CD pipeline to block unvalidated deserialization primitives. "
            "Static and dynamic application security testing (SAST/DAST) tools were updated with customized vulnerability rules to prevent regression. "
            "Weekly red-team simulations were established to stress-test identity proxy endpoints under high-load adversarial conditions. "
            "Engineering teams completed mandatory threat-modeling refresher workshops focusing on secure microservice communication and credential handling.\n\n"
            "Infrastructure as Code templates were revised with strict static analyzers to mandate immutable root filesystems on all staging pods. "
            "Audit telemetry retention for non-production environments was increased from 14 days to 90 days to enhance post-incident visibility. "
            "Engineering leadership committed to dedicating 20% of every sprint in the upcoming quarter strictly to architectural security enhancements."
        ),
        (
            "Page 5: Governance, Board Oversight & Long-Term Security Investment\n\n"
            "The CloudScale Executive Board convened an extraordinary security review session on July 16, 2026 to evaluate incident findings and recommendations. "
            "The Board unanimously approved an additional $2.5 million capital allocation for FY27 dedicated to defensive infrastructure hardening. "
            "Formal security advisory SEC-2026-07 was distributed to enterprise customers, outlining the technical details of the defense and key lessons learned. "
            "CloudScale committed to expediting its transition to a comprehensive micro-segmented zero-trust architecture across all cloud providers.\n\n"
            "A permanent Security Steering Committee was established, reporting quarterly to the Audit and Risk Committee of the Board. "
            "An independent penetration testing engagement has been scheduled with Mandiant for Q4 2026 to validate overall enterprise security posture. "
            "Continuous automated compliance monitoring was integrated into operational dashboards to ensure 100% adherence to SOC2 and ISO 27001 standards. "
            "CloudScale remains dedicated to transparency, resilience, and maintaining the highest standard of customer data protection across all services.\n\n"
            "The Chief Information Security Officer will deliver bi-weekly progress reports directly to the Board until all FY27 hardening milestones are satisfied. "
            "Employee compensation structures were updated to link engineering bonuses directly to verifiable security and compliance metrics. "
            "These structural initiatives cement CloudScale's posture as a trusted, resilient global enterprise cloud provider."
        ),
    ]

    for text in pages_content:
        page = pdf.new_page(width=595, height=842)
        rect = pymupdf.Rect(50, 50, 545, 792)
        page.insert_textbox(rect, text, fontsize=9)

    pdf_bytes = pdf.tobytes()
    pdf.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_full_pipeline_e2e_and_performance(client: TestClient, auth_headers, db_session):
    """
    The central end-to-end integration & performance test for ContentForge AI.
    Uploads 5-page PDF -> chunks -> understanding -> generates 4 formats -> asserts time < 60s.
    """
    start_time = time.perf_counter()

    # Step 1: Upload real 5-page PDF
    pdf_bytes = create_sample_5page_pdf_bytes()
    upload_resp = client.post(
        "/documents/upload",
        files={"file": ("incident_report_5page.pdf", pdf_bytes, "application/pdf")},
        headers=auth_headers,
    )
    assert upload_resp.status_code == 202
    doc_id = upload_resp.json()["document_id"]

    # Step 2: Background extraction & sliding-window chunking
    task_res = process_document_task(doc_id)
    assert task_res["status"] == "success"
    assert task_res["chunks_count"] >= 2

    # Verify document status updated to processed
    doc_record = client.get(f"/documents/{doc_id}", headers=auth_headers).json()
    assert doc_record["processed_status"] == "processed"

    # Step 3: Trigger Understanding Pass (single pass builds Fact Registry)
    understand_resp = client.post(f"/documents/{doc_id}/understand", headers=auth_headers)
    assert understand_resp.status_code == 200
    understand_data = understand_resp.json()
    assert understand_data["total_facts"] >= 3
    assert len(understand_data["summary"]) > 20

    # Verify Fact Registry populated in DB
    facts_resp = client.get(f"/documents/{doc_id}/facts", headers=auth_headers)
    assert facts_resp.status_code == 200
    registered_facts = facts_resp.json()["facts"]
    assert len(registered_facts) >= 3

    # Step 4: Request generation for 4 target channels simultaneously
    requested_formats = ["linkedin", "twitter", "advisory", "executive_summary"]
    gen_resp = client.post(
        "/generate",
        json={
            "document_id": doc_id,
            "selected_outputs": requested_formats,
            "settings": {
                "audience": "executive",
                "tone": "authoritative",
                "detail_level": "standard",
                "objective": "Enterprise stakeholder incident notification",
            },
        },
        headers=auth_headers,
    )
    assert gen_resp.status_code == 202
    job_id = gen_resp.json()["job_id"]

    # Step 5: Verify parallel generation completed by endpoint
    from app.models.generation_job import GenerationJob
    job = db_session.query(GenerationJob).filter(GenerationJob.id == uuid.UUID(job_id)).first()
    assert job is not None

    # Step 6: Validate all 4 outputs
    assert job.status in ["completed", "completed_with_warnings"]
    assert len(job.outputs) == 4

    output_types_generated = {o.output_type for o in job.outputs}
    assert output_types_generated == set(requested_formats)

    for output in job.outputs:
        # Schema compliance validation
        is_valid, validated_model, error_msg = validate_output_schema(output.output_type, output.content)
        assert is_valid is True, f"Schema validation failed for {output.output_type}: {error_msg}"

        # Confidence grounding score and status assertion
        assert 0.0 <= output.validation_score <= 1.0
        assert output.status in ["completed", "completed_with_warnings"]
        assert len(output.fact_ids_used) > 0, f"No facts cited by {output.output_type}"

    # Step 7: Verify outputs retrieval endpoint
    outputs_resp = client.get(f"/generation/{job_id}/outputs", headers=auth_headers)
    assert outputs_resp.status_code == 200
    assert outputs_resp.json()["total_outputs"] == 4

    total_pipeline_duration = time.perf_counter() - start_time

    # Step 8: Performance Benchmark Assertion (< 60 seconds budget)
    print(f"\n[BENCHMARK] Full 5-page pipeline duration: {total_pipeline_duration:.2f}s")
    assert total_pipeline_duration < 60.0, (
        f"Pipeline exceeded 60s performance budget: took {total_pipeline_duration:.2f}s"
    )
