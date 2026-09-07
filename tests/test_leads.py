def _create_customer(client, external_id: str = "CUST-L-001") -> int:
    response = client.post(
        "/api/customers",
        json={"Customer_ID": external_id, "CRM_Gender": "unknown"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_get_lead(client) -> None:
    customer_id = _create_customer(client, "CUST-L-002")

    payload = {
        "Customer_ID": customer_id,
        "CRM_Channel": "website",
        "CRM_Data_Medium": "organic",
        "Label_Source_Lead_Status": "new",
        "priority": "high",
    }

    create_response = client.post("/api/leads", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["customer_id"] == customer_id

    get_response = client.get(f"/api/leads/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["CRM_Channel"] == "website"


def test_list_update_and_delete_lead(client) -> None:
    customer_id = _create_customer(client, "CUST-L-003")

    create_response = client.post(
        "/api/leads",
        json={"Customer_ID": customer_id, "CRM_Channel": "email", "Label_Source_Lead_Status": "new", "priority": "medium"},
    )
    lead_id = create_response.json()["id"]

    list_response = client.get(f"/api/leads?customer_id={customer_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == lead_id for item in list_response.json())

    update_response = client.patch(f"/api/leads/{lead_id}", json={"status": "qualified", "priority": "high"})
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["Label_Source_Lead_Status"] == "qualified"
    assert updated["priority"] == "high"

    delete_response = client.delete(f"/api/leads/{lead_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/leads/{lead_id}")
    assert get_deleted.status_code == 404


def test_create_lead_with_invalid_customer_fails(client) -> None:
    response = client.post(
        "/api/leads",
        json={"Customer_ID": 999999, "CRM_Channel": "website", "Label_Source_Lead_Status": "new", "priority": "low"},
    )
    assert response.status_code == 400
    assert "customer_id" in response.json()["detail"]
