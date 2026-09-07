def _create_customer(client, external_id: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Report"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str, name: str, channel: str = "email") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": name, "channel": channel, "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int, status_value: str, source_channel: str = "email") -> int:
    response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": source_channel,
            "status": status_value,
            "priority": "medium",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_reports_endpoints(client) -> None:
    customer_id = _create_customer(client, "CUST-REP-001")
    campaign_a = _create_campaign(client, "CMP-REP-001", "Campaign A", "email")
    campaign_b = _create_campaign(client, "CMP-REP-002", "Campaign B", "website")

    lead_open = _create_lead(client, customer_id, campaign_a, "new", "email")
    _create_lead(client, customer_id, campaign_a, "converted", "email")
    _create_lead(client, customer_id, campaign_b, "qualified", "website")
    _create_lead(client, customer_id, campaign_b, "lost", "website")

    task_open = client.post(
        "/api/tasks",
        json={
            "lead_id": lead_open,
            "customer_id": customer_id,
            "title": "Open task",
            "status": "open",
        },
    )
    assert task_open.status_code == 201

    task_done = client.post(
        "/api/tasks",
        json={
            "lead_id": lead_open,
            "customer_id": customer_id,
            "title": "Done task",
            "status": "completed",
        },
    )
    assert task_done.status_code == 201

    followup_pending = client.post(
        "/api/followups",
        json={
            "task_id": task_open.json()["id"],
            "lead_id": lead_open,
            "customer_id": customer_id,
            "channel": "call",
            "status": "pending",
        },
    )
    assert followup_pending.status_code == 201

    followup_completed = client.post(
        "/api/followups",
        json={
            "task_id": task_done.json()["id"],
            "lead_id": lead_open,
            "customer_id": customer_id,
            "channel": "email",
            "status": "completed",
        },
    )
    assert followup_completed.status_code == 201

    campaign_report = client.get("/api/reports/campaign-performance")
    assert campaign_report.status_code == 200
    items = campaign_report.json()["items"]
    assert len(items) == 2
    by_code = {item["campaign_code"]: item for item in items}
    assert by_code["CMP-REP-001"]["lead_count"] == 2
    assert by_code["CMP-REP-001"]["converted_leads"] == 1
    assert by_code["CMP-REP-001"]["conversion_rate"] == 0.5

    workload_report = client.get("/api/reports/workload")
    assert workload_report.status_code == 200
    workload = workload_report.json()
    assert workload["total_tasks"] == 2
    assert workload["open_tasks"] == 1
    assert workload["completed_tasks"] == 1
    assert workload["total_followups"] == 2
    assert workload["pending_followups"] == 1
    assert workload["completed_followups"] == 1

    pipeline_report = client.get("/api/reports/pipeline")
    assert pipeline_report.status_code == 200
    pipeline = pipeline_report.json()
    assert pipeline["total_leads"] == 4
    assert pipeline["new_leads"] == 1
    assert pipeline["qualified_leads"] == 1
    assert pipeline["converted_leads"] == 1
    assert pipeline["lost_leads"] == 1
