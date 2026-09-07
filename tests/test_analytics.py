from app.models.engagement_event import EngagementEvent


def _create_customer(client, external_id: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Analytics"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str) -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Analytics Campaign", "channel": "email", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int, status_value: str, source_channel: str) -> int:
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


def test_analytics_overview_funnel_channels_and_dashboard(client, db_session) -> None:
    customer_id = _create_customer(client, "CUST-AN-001")
    campaign_id = _create_campaign(client, "CMP-AN-001")

    lead_new = _create_lead(client, customer_id, campaign_id, "new", "email")
    _create_lead(client, customer_id, campaign_id, "qualified", "website")
    _create_lead(client, customer_id, campaign_id, "converted", "website")
    _create_lead(client, customer_id, campaign_id, "lost", "phone")

    task_resp = client.post(
        "/api/tasks",
        json={
            "lead_id": lead_new,
            "customer_id": customer_id,
            "title": "Send proposal",
            "status": "open",
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    followup_resp = client.post(
        "/api/followups",
        json={
            "task_id": task_id,
            "lead_id": lead_new,
            "customer_id": customer_id,
            "channel": "call",
            "status": "pending",
        },
    )
    assert followup_resp.status_code == 201

    call_resp = client.post(
        "/api/calls",
        json={
            "lead_id": lead_new,
            "customer_id": customer_id,
            "direction": "outbound",
            "status": "scheduled",
            "phone_number": "+910000001111",
        },
    )
    assert call_resp.status_code == 201

    db_session.add_all(
        [
            EngagementEvent(
                lead_id=lead_new,
                customer_id=customer_id,
                campaign_id=campaign_id,
                channel="email",
                metric_type="sent",
                metric_value=2,
            ),
            EngagementEvent(
                lead_id=lead_new,
                customer_id=customer_id,
                campaign_id=campaign_id,
                channel="website",
                metric_type="clicked",
                metric_value=1,
            ),
        ]
    )
    db_session.commit()

    overview = client.get("/api/analytics/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["total_customers"] == 1
    assert overview_payload["total_leads"] == 4
    assert overview_payload["total_campaigns"] == 1
    assert overview_payload["total_calls"] == 1
    assert overview_payload["open_tasks"] == 1
    assert overview_payload["pending_followups"] == 1
    assert overview_payload["converted_leads"] == 1
    assert overview_payload["conversion_rate"] == 0.25

    funnel = client.get("/api/analytics/funnel")
    assert funnel.status_code == 200
    funnel_payload = funnel.json()
    assert funnel_payload["new_leads"] == 1
    assert funnel_payload["qualified_leads"] == 1
    assert funnel_payload["converted_leads"] == 1
    assert funnel_payload["lost_leads"] == 1
    assert funnel_payload["total_leads"] == 4
    assert funnel_payload["conversion_rate"] == 0.25

    channels = client.get("/api/analytics/channels")
    assert channels.status_code == 200
    channel_items = {item["channel"]: item for item in channels.json()["items"]}
    assert channel_items["email"]["lead_count"] == 1
    assert channel_items["email"]["engagement_events"] == 2
    assert channel_items["website"]["lead_count"] == 2
    assert channel_items["website"]["engagement_events"] == 1

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["total_leads"] == 4
