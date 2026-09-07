from datetime import UTC, datetime


def _create_customer(client, external_id: str, first_name: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": first_name},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str, name: str, channel: str) -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": name, "channel": channel, "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int, status_value: str, priority: str, source_channel: str) -> int:
    response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": source_channel,
            "status": status_value,
            "priority": priority,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_end_to_end_integration_flow(client) -> None:
    c1 = _create_customer(client, "CUST-INT-001", "IntA")
    c2 = _create_customer(client, "CUST-INT-002", "IntB")
    c3 = _create_customer(client, "CUST-INT-003", "IntC")

    campaign_id = _create_campaign(client, "CMP-INT-001", "Integration Campaign", "website")

    lead_new = _create_lead(client, c1, campaign_id, "new", "high", "website")
    _create_lead(client, c2, campaign_id, "qualified", "medium", "email")
    _create_lead(client, c3, campaign_id, "converted", "high", "website")

    task_response = client.post(
        "/api/tasks",
        json={
            "lead_id": lead_new,
            "customer_id": c1,
            "title": "Integration follow up",
            "status": "open",
            "priority": "high",
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    followup_response = client.post(
        "/api/followups",
        json={
            "task_id": task_id,
            "lead_id": lead_new,
            "customer_id": c1,
            "channel": "call",
            "status": "pending",
        },
    )
    assert followup_response.status_code == 201
    followup_id = followup_response.json()["id"]

    call_response = client.post(
        "/api/calls",
        json={
            "lead_id": lead_new,
            "customer_id": c1,
            "direction": "outbound",
            "status": "scheduled",
            "phone_number": "+910000009111",
        },
    )
    assert call_response.status_code == 201
    call_id = call_response.json()["id"]

    start_response = client.post(
        f"/api/calls/{call_id}/start",
        json={"started_at": datetime(2026, 9, 8, 12, 0, tzinfo=UTC).isoformat()},
    )
    assert start_response.status_code == 200

    end_response = client.post(
        f"/api/calls/{call_id}/end",
        json={"ended_at": datetime(2026, 9, 8, 12, 3, tzinfo=UTC).isoformat()},
    )
    assert end_response.status_code == 200
    assert end_response.json()["duration_seconds"] == 180

    train_response = client.post("/api/ml/train", json={"model_name": "lead_conversion_baseline"})
    assert train_response.status_code == 201

    analyze_response = client.post("/api/ai/analyze-lead", json={"lead_id": lead_new})
    assert analyze_response.status_code == 200
    assert len(analyze_response.json()["predictions"]) == 7

    decision_response = client.post("/api/decision/next-action", json={"lead_id": lead_new})
    assert decision_response.status_code == 200
    assert decision_response.json()["decision_type"] == "next_action"

    update_followup = client.patch(f"/api/followups/{followup_id}", json={"status": "completed"})
    assert update_followup.status_code == 200
    assert update_followup.json()["completed_at"] is not None

    analytics_overview = client.get("/api/analytics/overview")
    assert analytics_overview.status_code == 200
    overview = analytics_overview.json()
    assert overview["total_customers"] == 3
    assert overview["total_leads"] == 3
    assert overview["total_calls"] == 1

    reports_pipeline = client.get("/api/reports/pipeline")
    assert reports_pipeline.status_code == 200
    pipeline = reports_pipeline.json()
    assert pipeline["new_leads"] == 1
    assert pipeline["qualified_leads"] == 1
    assert pipeline["converted_leads"] == 1

    reports_workload = client.get("/api/reports/workload")
    assert reports_workload.status_code == 200
    workload = reports_workload.json()
    assert workload["total_tasks"] == 1
    assert workload["completed_followups"] == 1
