def _create_customer(client, external_id: str = "CUST-LIFE-001") -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Lifecycle"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str = "CMP-LIFE-001") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Lifecycle Campaign", "channel": "website", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_lead_lifecycle_details_assignment_timeline_and_outcome(client) -> None:
    customer_id = _create_customer(client, "CUST-LIFE-002")
    campaign_id = _create_campaign(client, "CMP-LIFE-002")

    lead_response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "website",
            "source_medium": "brochure",
            "status": "new",
            "priority": "high",
        },
    )
    assert lead_response.status_code == 201
    lead_id = lead_response.json()["id"]

    assign_response = client.post(
        f"/api/leads/{lead_id}/assign",
        json={"to_section": "ai_qualification", "to_handler": "ai-agent", "reason": "new lead"},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["to_section"] == "ai_qualification"

    transfer_response = client.post(
        f"/api/leads/{lead_id}/transfer",
        json={"to_section": "sales", "to_handler": "agent-101", "reason": "high intent"},
    )
    assert transfer_response.status_code == 200
    assert transfer_response.json()["assignment_type"] == "transfer"

    outcome_response = client.post(
        f"/api/leads/{lead_id}/outcomes",
        json={
            "action_type": "human_call",
            "outcome_code": "interested",
            "outcome_label": "Interested",
            "notes": "Customer asked for a callback",
            "followup_required": True,
            "next_action_hint": "call",
        },
    )
    assert outcome_response.status_code == 201
    assert outcome_response.json()["followup_required"] is True

    outcomes_list = client.get(f"/api/leads/{lead_id}/outcomes")
    assert outcomes_list.status_code == 200
    assert len(outcomes_list.json()) >= 1

    timeline_response = client.get(f"/api/leads/{lead_id}/timeline")
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    event_types = {item["event_type"] for item in timeline}
    assert "lead_created" in event_types
    assert "lead_transferred" in event_types or "lead_assigned" in event_types
    assert "outcome_recorded" in event_types
    assert "followup_created" in event_types

    details_response = client.get(f"/api/leads/{lead_id}/details")
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["lead"]["id"] == lead_id
    assert details["customer"]["id"] == customer_id
    assert details["campaign"]["id"] == campaign_id
    assert details["assignment"]["to_section"] == "sales"
    assert isinstance(details["timeline"], list)
    assert isinstance(details["outcomes"], list)
