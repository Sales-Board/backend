from app.models.website_event import WebsiteEvent


def _create_customer(client, external_id: str = "CUST-J-001") -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Journey"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str = "CMP-J-001") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Journey Campaign", "channel": "website", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int) -> int:
    response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "website",
            "status": "new",
            "priority": "medium",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_lead_journey_and_summary_endpoints(client, db_session) -> None:
    customer_id = _create_customer(client, "CUST-J-002")
    campaign_id = _create_campaign(client, "CMP-J-002")
    lead_id = _create_lead(client, customer_id, campaign_id)

    db_session.add_all(
        [
            WebsiteEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                event_name="page_view",
                step_name="landing",
                step_number=1,
                device_type="mobile",
                is_repeat_visitor=False,
                event_payload={"path": "/"},
            ),
            WebsiteEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                event_name="cta_click",
                step_name="quote_start",
                step_number=2,
                device_type="mobile",
                is_repeat_visitor=True,
                event_payload={"button": "start_quote"},
            ),
        ]
    )
    db_session.commit()

    lead_journey_resp = client.get(f"/api/leads/{lead_id}/journey")
    assert lead_journey_resp.status_code == 200
    lead_events = lead_journey_resp.json()
    assert len(lead_events) == 2
    assert {item["event_name"] for item in lead_events} == {"page_view", "cta_click"}

    summary_resp = client.get(f"/api/journey/leads/{lead_id}")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["lead_id"] == lead_id
    assert summary["total_events"] == 2
    assert summary["unique_event_names"] == ["cta_click", "page_view"]


def test_website_journey_filters(client, db_session) -> None:
    customer_id = _create_customer(client, "CUST-J-003")
    campaign_id = _create_campaign(client, "CMP-J-003")
    lead_id = _create_lead(client, customer_id, campaign_id)

    db_session.add_all(
        [
            WebsiteEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                event_name="page_view",
                step_name="landing",
                step_number=1,
                device_type="desktop",
                is_repeat_visitor=False,
                event_payload={"path": "/home"},
            ),
            WebsiteEvent(
                lead_id=lead_id,
                customer_id=customer_id,
                event_name="form_submit",
                step_name="proposal",
                step_number=3,
                device_type="mobile",
                is_repeat_visitor=True,
                event_payload={"form": "lead_capture"},
            ),
        ]
    )
    db_session.commit()

    by_lead_resp = client.get(f"/api/journey/website?lead_id={lead_id}")
    assert by_lead_resp.status_code == 200
    assert len(by_lead_resp.json()) == 2

    by_device_resp = client.get("/api/journey/website?device_type=mobile")
    assert by_device_resp.status_code == 200
    events = by_device_resp.json()
    assert len(events) == 1
    assert events[0]["event_name"] == "form_submit"
