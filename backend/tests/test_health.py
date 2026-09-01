"""
backend/tests/test_health.py

Test /health and /api/v1/ping endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "app_name" in data


def test_api_v1_ping_endpoint():
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pong"
    assert data["version"] == "v1"
