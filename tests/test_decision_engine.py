def _create_customer(client, external_id: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Decision"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str) -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Decision Campaign", "channel": "email", "status": "active"},
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


def _seed_min_training(client) -> tuple[int, int]:
    c1 = _create_customer(client, "CUST-DEC-001")
    c2 = _create_customer(client, "CUST-DEC-002")
    c3 = _create_customer(client, "CUST-DEC-003")
    camp = _create_campaign(client, "CMP-DEC-001")

    lead_id = _create_lead(client, c1, camp, "qualified", "high", "website")
    _create_lead(client, c2, camp, "new", "low", "email")
    _create_lead(client, c3, camp, "converted", "high", "website")

    train_response = client.post("/api/ml/train", json={"model_name": "lead_conversion_baseline"})
    assert train_response.status_code == 201
    return lead_id, c1


def test_decision_next_action_and_logs(client) -> None:
    lead_id, customer_id = _seed_min_training(client)

    decide = client.post("/api/decision/next-action", json={"lead_id": lead_id})
    assert decide.status_code == 200
    payload = decide.json()
    assert payload["decision_type"] == "next_action"
    assert payload["recommended_action"]
    assert payload["priority"] in {"high", "medium", "low"}
    assert 0.0 <= payload["confidence"] <= 1.0

    lead_logs = client.get(f"/api/decision/leads/{lead_id}")
    assert lead_logs.status_code == 200
    assert len(lead_logs.json()) >= 1

    customer_logs = client.get(f"/api/decision/customers/{customer_id}")
    assert customer_logs.status_code == 200
    assert len(customer_logs.json()) >= 1


def test_decision_validation_errors(client) -> None:
    missing_subject = client.post("/api/decision/next-action", json={})
    assert missing_subject.status_code == 400
    assert "lead_id or customer_id" in missing_subject.json()["detail"]

    missing_lead = client.post("/api/decision/next-action", json={"lead_id": 999999})
    assert missing_lead.status_code == 404
    assert "Lead not found" in missing_lead.json()["detail"]
