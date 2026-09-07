from datetime import UTC, datetime


def _create_customer(client, external_id: str = "CUST-CALL-001") -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Call Owner"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str = "CMP-CALL-001") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Call Campaign", "channel": "phone", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int) -> int:
    response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "phone",
            "status": "new",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_call_crud_and_lead_calls_endpoint(client) -> None:
    customer_id = _create_customer(client, "CUST-CALL-002")
    campaign_id = _create_campaign(client, "CMP-CALL-002")
    lead_id = _create_lead(client, customer_id, campaign_id)

    payload = {
        "lead_id": lead_id,
        "customer_id": customer_id,
        "direction": "outbound",
        "status": "scheduled",
        "phone_number": "+910000000777",
        "notes": "initial follow-up",
    }
    create_response = client.post("/api/calls", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    call_id = created["id"]
    assert created["lead_id"] == lead_id

    get_response = client.get(f"/api/calls/{call_id}")
    assert get_response.status_code == 200
    assert get_response.json()["phone_number"] == "+910000000777"

    list_response = client.get(f"/api/calls?lead_id={lead_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == call_id for item in list_response.json())

    lead_calls_response = client.get(f"/api/leads/{lead_id}/calls")
    assert lead_calls_response.status_code == 200
    assert any(item["id"] == call_id for item in lead_calls_response.json())

    update_response = client.patch(f"/api/calls/{call_id}", json={"notes": "rescheduled", "status": "scheduled"})
    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "rescheduled"

    delete_response = client.delete(f"/api/calls/{call_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/calls/{call_id}")
    assert missing_response.status_code == 404


def test_call_start_and_end_lifecycle(client) -> None:
    customer_id = _create_customer(client, "CUST-CALL-003")
    campaign_id = _create_campaign(client, "CMP-CALL-003")
    lead_id = _create_lead(client, customer_id, campaign_id)

    create_response = client.post(
        "/api/calls",
        json={
            "lead_id": lead_id,
            "customer_id": customer_id,
            "direction": "inbound",
            "status": "scheduled",
            "phone_number": "+910000000888",
        },
    )
    call_id = create_response.json()["id"]

    started_at = datetime(2026, 9, 7, 12, 0, 0, tzinfo=UTC).isoformat()
    end_at = datetime(2026, 9, 7, 12, 5, 30, tzinfo=UTC).isoformat()

    start_response = client.post(f"/api/calls/{call_id}/start", json={"started_at": started_at})
    assert start_response.status_code == 200
    started = start_response.json()
    assert started["CDR_Top_Call_Status"] == "in_progress"
    assert started["started_at"].startswith("2026-09-07T12:00:00")

    end_response = client.post(
        f"/api/calls/{call_id}/end",
        json={"ended_at": end_at, "notes": "customer requested callback"},
    )
    assert end_response.status_code == 200
    ended = end_response.json()
    assert ended["CDR_Top_Call_Status"] == "completed"
    assert ended["CDR_Avg_Talk_Sec"] == 330
    assert ended["notes"] == "customer requested callback"


def test_call_reference_validation(client) -> None:
    response = client.post(
        "/api/calls",
        json={
            "lead_id": 999999,
            "customer_id": 999999,
            "direction": "outbound",
            "status": "scheduled",
            "phone_number": "+910000001999",
        },
    )
    assert response.status_code == 400
    assert "lead_id" in response.json()["detail"]
