"""
ContentForge AI Load Test Suite (Locust).
Simulates 50 concurrent operators uploading documents and triggering multi-format generation jobs.
Validates that Celery/Redis backpressure queues requests gracefully without API 500 crashes.
"""

import json
import logging
import os
import random
import uuid
from locust import HttpUser, task, between, events

logger = logging.getLogger("locust.contentforge")

# Sample text documents for realistic load simulation
SAMPLE_TEXTS = [
    (
        "Incident Telemetry: Cloud Database Outage in us-east-1 on July 14, 2026. "
        "Primary database failover initiated due to hardware partition. "
        "Application connection pools experienced 18 minutes of latency. "
        "No persistent transactions were corrupted. Mitigation actions completed."
    ),
    (
        "Security Advisory: CVE-2026-9011 Zero-Day vulnerability in API routing proxy. "
        "Allows unauthorized header tampering. Assigned CVSS score 8.7. "
        "Operators must deploy hotfix v3.1.2 immediately across all edge clusters."
    ),
    (
        "Technical Architecture Report: Adopting eBPF observability reduced CPU overhead from 6% to 0.7%. "
        "Packet capture spans 300 microservices without code modifications. "
        "Continuous profiling enabled across Kubernetes nodes."
    ),
]

TARGET_OUTPUT_COMBINATIONS = [
    ["linkedin", "twitter"],
    ["advisory", "executive_summary"],
    ["linkedin", "twitter", "advisory", "executive_summary"],
]


class ContentForgeUser(HttpUser):
    # Wait between 1 and 3 seconds between actions
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate user and obtain JWT token for subsequent API calls."""
        # Use seeded test user or register dynamically
        self.email = f"loadtest_{uuid.uuid4().hex[:8]}@contentforge.ai"
        self.password = "LoadTestPass123!"
        self.auth_headers = {}
        self.document_ids = []

        # Attempt login, if not exists, register first
        login_res = self.client.post(
            "/auth/login",
            json={"email": "operator@acmelabs.com", "password": "ValidPass123!"},
        )
        if login_res.status_code == 200:
            token = login_res.json().get("access_token")
            self.auth_headers = {"Authorization": f"Bearer {token}"}
        else:
            # Fallback: test without token or use bearer token directly if preconfigured
            token = os.getenv("LOAD_TEST_JWT_TOKEN", "")
            if token:
                self.auth_headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def upload_document(self):
        """Simulate document text ingestion."""
        text_sample = random.choice(SAMPLE_TEXTS)
        resp = self.client.post(
            "/documents/upload",
            data={
                "raw_text": text_sample,
                "sensitivity_flag": "internal",
            },
            headers=self.auth_headers,
            name="/documents/upload",
        )
        if resp.status_code == 202:
            data = resp.json()
            doc_id = data.get("document_id")
            if doc_id:
                self.document_ids.append(doc_id)
                # Keep last 5 documents in memory
                if len(self.document_ids) > 5:
                    self.document_ids.pop(0)

    @task(5)
    def trigger_generation_job(self):
        """
        Simulate triggering an expensive multi-format generation job.
        Validates API responds 202 Accepted and queues under load.
        """
        if not self.document_ids:
            # First upload a document if none exists
            self.upload_document()
            if not self.document_ids:
                return

        doc_id = random.choice(self.document_ids)
        outputs = random.choice(TARGET_OUTPUT_COMBINATIONS)

        payload = {
            "document_id": doc_id,
            "selected_outputs": outputs,
            "settings": {
                "audience": "executive",
                "tone": "authoritative",
                "detail_level": "standard",
            },
        }

        with self.client.post(
            "/generate",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
            name="/generate",
        ) as response:
            if response.status_code == 202:
                response.success()
                job_id = response.json().get("job_id")
                # Optionally poll job status
                if job_id:
                    self.client.get(
                        f"/generation/{job_id}",
                        headers=self.auth_headers,
                        name="/generation/{id}",
                    )
            elif response.status_code == 429:
                # Rate limit is expected and valid under stress test
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code} - {response.text}")

    @task(2)
    def check_health_and_metrics(self):
        """Simulate monitoring probes under heavy load."""
        self.client.get("/health", name="/health")
        self.client.get("/metrics", name="/metrics")
