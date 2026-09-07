def _create_customer(client, external_id: str = "CUST-TASK-001") -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Task Owner"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str = "CMP-TASK-001") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Task Campaign", "channel": "phone", "status": "active"},
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
            "priority": "medium",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_task_crud(client) -> None:
    customer_id = _create_customer(client, "CUST-TASK-002")
    campaign_id = _create_campaign(client, "CMP-TASK-002")
    lead_id = _create_lead(client, customer_id, campaign_id)

    list_empty = client.get("/api/tasks")
    assert list_empty.status_code == 200
    assert list_empty.json() == []

    create_response = client.post(
        "/api/tasks",
        json={
            "lead_id": lead_id,
            "customer_id": customer_id,
            "title": "Call back lead",
            "description": "Follow up this afternoon",
            "status": "open",
            "priority": "high",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    task_id = created["id"]
    assert created["Label_Source_Disposition"] == "Call back lead"

    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    patch_response = client.patch(f"/api/tasks/{task_id}", json={"status": "in_progress"})
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "in_progress"

    filtered = client.get(f"/api/tasks?lead_id={lead_id}&status_filter=in_progress")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    delete_response = client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 204

    missing = client.get(f"/api/tasks/{task_id}")
    assert missing.status_code == 404


def test_followups_create_list_update(client) -> None:
    customer_id = _create_customer(client, "CUST-TASK-003")
    campaign_id = _create_campaign(client, "CMP-TASK-003")
    lead_id = _create_lead(client, customer_id, campaign_id)

    task_response = client.post(
        "/api/tasks",
        json={
            "lead_id": lead_id,
            "customer_id": customer_id,
            "title": "Prepare proposal",
            "status": "open",
            "priority": "medium",
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    create_followup = client.post(
        "/api/followups",
        json={
            "task_id": task_id,
            "lead_id": lead_id,
            "customer_id": customer_id,
            "channel": "call",
            "notes": "Schedule a callback",
            "status": "pending",
        },
    )
    assert create_followup.status_code == 201
    followup = create_followup.json()
    followup_id = followup["id"]
    assert followup["task_id"] == task_id

    list_followups = client.get(f"/api/followups?task_id={task_id}")
    assert list_followups.status_code == 200
    assert len(list_followups.json()) == 1

    update_followup = client.patch(
        f"/api/followups/{followup_id}",
        json={"status": "completed", "notes": "Customer responded positively"},
    )
    assert update_followup.status_code == 200
    updated = update_followup.json()
    assert updated["status"] == "completed"
    assert updated["completed_at"] is not None


def test_task_and_followup_reference_validation(client) -> None:
    bad_task = client.post(
        "/api/tasks",
        json={
            "lead_id": 999999,
            "customer_id": 999999,
            "title": "Invalid links",
        },
    )
    assert bad_task.status_code == 400

    bad_followup = client.post(
        "/api/followups",
        json={
            "task_id": 999999,
            "lead_id": 999999,
            "customer_id": 999999,
            "channel": "call",
            "status": "pending",
        },
    )
    assert bad_followup.status_code == 400
