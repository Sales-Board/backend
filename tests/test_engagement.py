from app.models.engagement_event import EngagementEvent


def _seed_context(client) -> tuple[int, int, int]:
    customer_resp = client.post(
        "/api/customers",
        json={"external_customer_id": "CUST-ENG-001", "first_name": "Engage"},
    )
    customer_id = customer_resp.json()["id"]

    campaign_resp = client.post(
        "/api/campaigns",
        json={"code": "CMP-ENG-001", "name": "Engagement Campaign", "channel": "whatsapp", "status": "active"},
    )
    campaign_id = campaign_resp.json()["id"]

    lead_resp = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "whatsapp",
            "status": "new",
            "priority": "medium",
        },
    )
    lead_id = lead_resp.json()["id"]
    return customer_id, campaign_id, lead_id


def test_engagement_channel_endpoints(client, db_session) -> None:
    customer_id, campaign_id, lead_id = _seed_context(client)

    db_session.add_all(
        [
            EngagementEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                campaign_id=campaign_id,
                channel="whatsapp",
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
                channel="website",
                metric_type="clicked",
                metric_value=1,
            ),
        ]
    )
    db_session.commit()

    whatsapp_resp = client.get(f"/api/engagement/whatsapp?campaign_id={campaign_id}")
    assert whatsapp_resp.status_code == 200
    whatsapp_events = whatsapp_resp.json()
    assert len(whatsapp_events) == 1
    assert whatsapp_events[0]["CRM_Channel"] == "whatsapp"

    email_resp = client.get("/api/engagement/email")
    assert email_resp.status_code == 200
    assert any(item["CRM_Channel"] == "email" for item in email_resp.json())

    website_resp = client.get(f"/api/engagement/website?lead_id={lead_id}")
    assert website_resp.status_code == 200
    website_events = website_resp.json()
    assert len(website_events) == 1
    assert website_events[0]["metric_type"] == "clicked"

    rcs_resp = client.get("/api/engagement/rcs")
    assert rcs_resp.status_code == 200
    assert rcs_resp.json() == []
