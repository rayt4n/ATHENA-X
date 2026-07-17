"""Tests for /health/* endpoints."""
from fastapi.testclient import TestClient
from athena_x_backend.main import app


def test_live_endpoint():
    client = TestClient(app)
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


def test_ready_endpoint():
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 200
