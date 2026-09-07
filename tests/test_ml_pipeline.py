import json
from pathlib import Path


def _create_customer(client, external_id: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "ML"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str) -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "ML Campaign", "channel": "email", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int, status_value: str, priority: str, channel: str) -> int:
    response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": channel,
            "status": status_value,
            "priority": priority,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_ml_training_and_model_listing(client) -> None:
    c1 = _create_customer(client, "CUST-ML-001")
    c2 = _create_customer(client, "CUST-ML-002")
    c3 = _create_customer(client, "CUST-ML-003")
    camp = _create_campaign(client, "CMP-ML-001")

    l1 = _create_lead(client, c1, camp, "qualified", "high", "website")
    l2 = _create_lead(client, c2, camp, "new", "low", "email")
    l3 = _create_lead(client, c3, camp, "converted", "high", "website")

    client.post(
        "/api/calls",
        json={"lead_id": l1, "customer_id": c1, "status": "completed", "direction": "outbound"},
    )
    client.post(
        "/api/calls",
        json={"lead_id": l3, "customer_id": c3, "status": "completed", "direction": "outbound"},
    )

    train_response = client.post("/api/ml/train", json={"model_name": "lead_conversion_baseline"})
    assert train_response.status_code == 201
    train_payload = train_response.json()
    assert train_payload["status"] == "completed"
    assert train_payload["training_rows"] >= 3
    assert train_payload["artifact_path"] is not None

    artifact_path = Path(train_payload["artifact_path"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["model_name"] == "lead_conversion_baseline"
    assert "global_positive_rate" in artifact

    job_id = train_payload["id"]
    job_response = client.get(f"/api/ml/train/{job_id}")
    assert job_response.status_code == 200
    assert job_response.json()["id"] == job_id

    models_response = client.get("/api/ml/models")
    assert models_response.status_code == 200
    models = models_response.json()
    assert any(item["model_name"] == "lead_conversion_baseline" for item in models)


def test_ml_training_requires_minimum_rows(client) -> None:
    c1 = _create_customer(client, "CUST-ML-010")
    camp = _create_campaign(client, "CMP-ML-010")
    _create_lead(client, c1, camp, "new", "low", "email")

    train_response = client.post("/api/ml/train", json={"model_name": "tiny_model"})
    assert train_response.status_code == 400
    assert "at least 3 leads" in train_response.json()["detail"]
