import pytest
from fastapi.testclient import TestClient
from app.models.user import User, UserRole
from app.core.security import create_access_token


def test_evaluation_report_endpoint_rbac(client: TestClient, auth_headers):
    """
    Verify operator cannot access admin evaluation report (403 Forbidden).
    """
    # auth_headers is standard operator role
    resp = client.get("/admin/evaluation-report", headers=auth_headers)
    assert resp.status_code == 403


def test_evaluation_report_endpoint_success(client: TestClient, admin_auth_headers):
    """
    Verify admin user can retrieve the latest evaluation report.
    """
    resp = client.get("/admin/evaluation-report", headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "timestamp" in data
    assert "overall_metrics" in data
    metrics = data["overall_metrics"]
    assert "faithfulness" in metrics
    assert "answer_relevancy" in metrics
    assert "contextual_recall" in metrics
    assert "composite_score" in metrics
    assert metrics["composite_score"] > 0.0
    assert "document_breakdown" in data
