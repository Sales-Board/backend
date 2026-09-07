from app.models.engagement_event import EngagementEvent


def _create_customer(client, external_id: str) -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Campaign Owner"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str = "CMP-001") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Q4 Push", "channel": "email", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_campaign_crud(client) -> None:
    campaign_id = _create_campaign(client, "CMP-CRUD-001")

    get_response = client.get(f"/api/campaigns/{campaign_id}")
    assert get_response.status_code == 200
    assert get_response.json()["code"] == "CMP-CRUD-001"

    update_response = client.patch(
        f"/api/campaigns/{campaign_id}",
        json={"name": "Q4 Push Updated", "status": "paused"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["CRM_UTM_Campaign"] == "Q4 Push Updated"
    assert updated["status"] == "paused"

    delete_response = client.delete(f"/api/campaigns/{campaign_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/campaigns/{campaign_id}")
    assert get_deleted.status_code == 404


def test_campaign_leads_and_performance(client, db_session) -> None:
    campaign_id = _create_campaign(client, "CMP-PERF-001")
    customer_id = _create_customer(client, "CUST-CMP-001")

    lead_response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "website",
            "source_medium": "organic",
            "status": "new",
            "priority": "high",
        },
    )
    assert lead_response.status_code == 201
    lead_id = lead_response.json()["id"]

    leads_response = client.get(f"/api/campaigns/{campaign_id}/leads")
    assert leads_response.status_code == 200
    leads = leads_response.json()
    assert any(item["id"] == lead_id for item in leads)

    db_session.add_all(
        [
            EngagementEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                campaign_id=campaign_id,
                channel="email",
                metric_type="sent",
                metric_value=1,
            ),
            EngagementEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                campaign_id=campaign_id,
                channel="email",
                metric_type="opened",
                metric_value=1,
            ),
            EngagementEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                campaign_id=campaign_id,
                channel="whatsapp",
                metric_type="sent",
                metric_value=1,
            ),
        ]
    )
    db_session.commit()

    perf_response = client.get(f"/api/campaigns/{campaign_id}/performance")
    assert perf_response.status_code == 200
    payload = perf_response.json()
    assert payload["campaign_id"] == campaign_id
    assert payload["total_events"] == 3
    assert payload["by_channel"]["email"] == 2
    assert payload["by_channel"]["whatsapp"] == 1
    assert payload["by_metric"]["sent"] == 2
    assert payload["by_metric"]["opened"] == 1


def test_campaign_code_conflict(client) -> None:
    payload = {"code": "CMP-DUP-001", "name": "Duplicate Campaign", "channel": "email", "status": "active"}

    first = client.post("/api/campaigns", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/campaigns", json=payload)
    assert duplicate.status_code == 409
