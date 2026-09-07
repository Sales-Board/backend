def _create_customer(client, external_id: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Perf"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str, channel: str) -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Perf Campaign", "channel": channel, "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_performance_smoke_high_volume_analytics_and_reports(client) -> None:
    campaign_email = _create_campaign(client, "CMP-PERF-001", "email")
    campaign_web = _create_campaign(client, "CMP-PERF-002", "website")

    total = 60
    for idx in range(total):
        customer_id = _create_customer(client, f"CUST-PERF-{idx:03d}")
        campaign_id = campaign_email if idx % 2 == 0 else campaign_web
        status_value = "converted" if idx % 3 == 0 else "new"
        source_channel = "email" if idx % 2 == 0 else "website"

        lead_response = client.post(
            "/api/leads",
            json={
                "customer_id": customer_id,
                "campaign_id": campaign_id,
                "source_channel": source_channel,
                "status": status_value,
                "priority": "high" if idx % 5 == 0 else "medium",
            },
        )
        assert lead_response.status_code == 201
        lead_id = lead_response.json()["id"]

        if idx < 20:
            task_response = client.post(
                "/api/tasks",
                json={
                    "lead_id": lead_id,
                    "customer_id": customer_id,
                    "title": f"Task {idx}",
                    "status": "open",
                },
            )
            assert task_response.status_code == 201
            task_id = task_response.json()["id"]
            followup_response = client.post(
                "/api/followups",
                json={
                    "task_id": task_id,
                    "lead_id": lead_id,
                    "customer_id": customer_id,
                    "channel": "call",
                    "status": "pending",
                },
            )
            assert followup_response.status_code == 201

    overview = client.get("/api/analytics/overview")
    assert overview.status_code == 200
    assert overview.json()["total_leads"] == total

    funnel = client.get("/api/analytics/funnel")
    assert funnel.status_code == 200
    assert funnel.json()["total_leads"] == total

    channels = client.get("/api/analytics/channels")
    assert channels.status_code == 200
    assert len(channels.json()["items"]) >= 2

    campaign_report = client.get("/api/reports/campaign-performance")
    assert campaign_report.status_code == 200
    assert len(campaign_report.json()["items"]) == 2

    workload_report = client.get("/api/reports/workload")
    assert workload_report.status_code == 200
    assert workload_report.json()["total_tasks"] == 20
