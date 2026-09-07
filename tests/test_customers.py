def test_create_and_get_customer(client) -> None:
    payload = {
        "Customer_ID": "CUST-001",
        "CRM_Gender": "female",
        "CRM_Age_Band": "26-35",
        "email": "asha@example.com",
        "phone": "+910000000001",
    }

    create_response = client.post("/api/customers", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["Customer_ID"] == payload["Customer_ID"]
    assert created["CRM_Gender"] == "female"
    assert created["CRM_Age_Band"] == "26-35"
    assert created["id"] > 0

    get_response = client.get(f"/api/customers/{created['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["Customer_ID"] == "CUST-001"


def test_list_update_and_delete_customer(client) -> None:
    create_response = client.post(
        "/api/customers",
        json={"Customer_ID": "CUST-002", "CRM_Gender": "male"},
    )
    customer_id = create_response.json()["id"]

    list_response = client.get("/api/customers")
    assert list_response.status_code == 200
    assert any(item["id"] == customer_id for item in list_response.json())

    update_response = client.patch(f"/api/customers/{customer_id}", json={"CRM_Occupation": "Engineer"})
    assert update_response.status_code == 200
    assert update_response.json()["CRM_Occupation"] == "Engineer"

    delete_response = client.delete(f"/api/customers/{customer_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/customers/{customer_id}")
    assert get_deleted.status_code == 404


def test_unique_external_customer_id_conflict(client) -> None:
    payload = {"Customer_ID": "CUST-003", "CRM_Gender": "female"}

    first = client.post("/api/customers", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/customers", json=payload)
    assert duplicate.status_code == 409
    assert "unique" in duplicate.json()["detail"]
