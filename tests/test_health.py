VALID_DB_STATES = {"not_configured", "connected", "unavailable"}


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] in VALID_DB_STATES


def test_health_endpoint_versioned(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] in VALID_DB_STATES
