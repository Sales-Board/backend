from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
VALID_DB_STATES = {"not_configured", "connected", "unavailable"}


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] in VALID_DB_STATES


def test_health_endpoint_versioned() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] in VALID_DB_STATES
