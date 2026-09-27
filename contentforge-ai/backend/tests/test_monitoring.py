import pytest
from fastapi.testclient import TestClient


def test_unified_health_check_endpoint(client: TestClient):
    """
    Test GET /health verifies database, redis, minio, and ollama dependencies.
    """
    resp = client.get("/health")
    assert resp.status_code in [200, 503]
    data = resp.json()
    assert "status" in data
    assert "dependencies" in data
    deps = data["dependencies"]
    assert "database" in deps
    assert "redis" in deps
    assert "minio" in deps
    assert "ollama" in deps
    assert deps["database"]["status"] == "up"


def test_prometheus_metrics_endpoint(client: TestClient):
    """
    Test GET /metrics returns valid Prometheus exposition format.
    """
    resp = client.get("/metrics")
    assert resp.status_code == 200
    metrics_text = resp.text
    # Check for standard process / python metrics
    assert "python_gc_objects_collected_total" in metrics_text or "process_cpu_seconds_total" in metrics_text
    # Check for custom ContentForge AI metrics
    assert "contentforge_ai_generation_duration_seconds" in metrics_text or "contentforge_" in metrics_text
