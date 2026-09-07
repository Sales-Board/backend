def test_create_and_get_product(client) -> None:
    payload = {
        "code": "PROD-TERM-001",
        "name": "Term Life Plan",
    }

    create_response = client.post("/api/products", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["CRM_Product_Code"] == payload["code"]

    get_response = client.get(f"/api/products/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["CRM_Product_Name"] == "Term Life Plan"


def test_list_update_and_delete_product(client) -> None:
    create_response = client.post(
        "/api/products",
        json={"code": "PROD-ULIP-001", "name": "ULIP Growth"},
    )
    product_id = create_response.json()["id"]

    list_response = client.get("/api/products")
    assert list_response.status_code == 200
    assert any(item["id"] == product_id for item in list_response.json())

    update_response = client.patch(
        f"/api/products/{product_id}",
        json={"name": "ULIP Growth Plus"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["CRM_Product_Name"] == "ULIP Growth Plus"

    delete_response = client.delete(f"/api/products/{product_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/products/{product_id}")
    assert get_deleted.status_code == 404


def test_unique_product_code_conflict(client) -> None:
    payload = {"code": "PROD-DUP-001", "name": "Duplicate Product"}

    first = client.post("/api/products", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/products", json=payload)
    assert duplicate.status_code == 409
    assert "unique" in duplicate.json()["detail"]
