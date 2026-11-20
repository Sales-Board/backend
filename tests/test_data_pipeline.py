import base64
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook

from app.core.excel_contract import (
    CALL_COLUMNS,
    CAMPAIGN_COLUMNS,
    CUSTOMER_COLUMNS,
    EVENT_COLUMNS,
    LEAD_COLUMNS,
    MESSAGE_COLUMNS,
    PRODUCT_COLUMNS,
    TARGET_COLUMNS,
    WEB_COLUMNS,
)


def _create_customer(client, external_id: str = "CUST-DATA-001") -> int:
    response = client.post(
        "/api/customers",
        json={"external_customer_id": external_id, "first_name": "Data"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client, code: str = "CMP-DATA-001") -> int:
    response = client.post(
        "/api/campaigns",
        json={"code": code, "name": "Data Campaign", "channel": "email", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_lead(client, customer_id: int, campaign_id: int) -> int:
    response = client.post(
        "/api/leads",
        json={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "email",
            "status": "new",
            "priority": "medium",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_data_import_and_history(client, tmp_path: Path) -> None:
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text("external_customer_id,first_name\nC100,Asha\n,MissingId\n", encoding="utf-8")

    import_response = client.post(
        "/api/data/import",
        json={
            "source_path": str(csv_path),
            "dataset_name": "customers",
            "file_format": "csv",
        },
    )
    assert import_response.status_code == 201
    payload = import_response.json()
    assert payload["status"] == "completed"
    assert payload["row_count"] == 2
    assert payload["valid_row_count"] == 1
    assert payload["invalid_row_count"] == 1

    job_id = payload["id"]
    by_id_response = client.get(f"/api/data/import/{job_id}")
    assert by_id_response.status_code == 200
    assert by_id_response.json()["id"] == job_id

    history_response = client.get("/api/data/history")
    assert history_response.status_code == 200
    assert any(item["id"] == job_id for item in history_response.json())


def test_data_quality_validation_and_export(client) -> None:
    customer_id = _create_customer(client, "CUST-DATA-002")
    campaign_id = _create_campaign(client, "CMP-DATA-002")
    lead_id = _create_lead(client, customer_id, campaign_id)

    call_response = client.post(
        "/api/calls",
        json={
            "lead_id": lead_id,
            "customer_id": customer_id,
            "direction": "outbound",
            "status": "scheduled",
            "phone_number": "+910000009999",
        },
    )
    assert call_response.status_code == 201
    call_id = call_response.json()["id"]

    started_at = datetime(2026, 9, 8, 10, 0, 0, tzinfo=UTC).isoformat()
    ended_at = datetime(2026, 9, 8, 9, 59, 0, tzinfo=UTC).isoformat()
    start_response = client.post(f"/api/calls/{call_id}/start", json={"started_at": started_at})
    assert start_response.status_code == 200
    end_response = client.post(f"/api/calls/{call_id}/end", json={"ended_at": ended_at})
    assert end_response.status_code == 200

    quality_response = client.get("/api/data/quality")
    assert quality_response.status_code == 200
    quality = quality_response.json()
    assert quality["table_counts"]["customers"] >= 1
    assert quality["table_counts"]["leads"] >= 1
    assert quality["table_counts"]["calls"] >= 1

    validation_response = client.get("/api/data/validation")
    assert validation_response.status_code == 200
    validation = validation_response.json()
    issue_codes = {issue["code"] for issue in validation["issues"]}
    assert "CALL_END_BEFORE_START" in issue_codes

    export_response = client.post("/api/data/export", json={"resource": "leads", "file_format": "json"})
    assert export_response.status_code == 201
    export_payload = export_response.json()
    assert export_payload["status"] == "completed"
    assert export_payload["resource"] == "leads"
    assert Path(export_payload["file_path"]).exists()


def test_data_load_previews_merges_and_skips_append_duplicates(client) -> None:
    created = client.post(
        "/api/customers",
        json={"external_customer_id": "CUST-LOAD-001", "crm_gender": "Female"},
    )
    assert created.status_code == 201
    customer_id = created.json()["id"]
    payload = {
        "dataset_name": "customers",
        "file_name": "customers.csv",
        "file_format": "csv",
        "content": (
            "external_customer_id,crm_gender,custom_source\n"
            "CUST-LOAD-001,,web\n"
            "CUST-LOAD-002,Male,upload\n"
        ),
    }

    preview = client.post("/api/data/load/preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["insert_count"] == 1
    assert preview.json()["update_count"] == 1
    assert preview.json()["invalid_count"] == 0

    applied = client.post("/api/data/load/apply", json={**payload, "mode": "merge"})
    assert applied.status_code == 201
    assert applied.json()["inserted_count"] == 1
    assert applied.json()["updated_count"] == 1

    existing = client.get(f"/api/customers/{customer_id}").json()
    assert existing["CRM_Gender"] == "Female"
    assert existing["Excel_Fields"]["custom_source"] == "web"

    appended = client.post("/api/data/load/apply", json={**payload, "mode": "append"})
    assert appended.status_code == 201
    assert appended.json()["inserted_count"] == 0
    assert appended.json()["skipped_count"] == 2


def test_data_load_replace_reports_and_removes_unlisted_records(client) -> None:
    for code, name in (("LOAD-P1", "Old one"), ("LOAD-P2", "Old two")):
        response = client.post("/api/products", json={"code": code, "name": name})
        assert response.status_code == 201

    payload = {
        "dataset_name": "products",
        "file_name": "products.json",
        "file_format": "json",
        "content": '[{"code":"LOAD-P1","name":"Updated one"},{"code":"LOAD-P3","name":"New three"}]',
    }
    preview = client.post("/api/data/load/preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["replace_delete_count"] == 1
    assert preview.json()["replace_blocked_count"] == 0

    applied = client.post("/api/data/load/apply", json={**payload, "mode": "replace"})
    assert applied.status_code == 201
    assert applied.json()["updated_count"] == 1
    assert applied.json()["inserted_count"] == 1
    assert applied.json()["deleted_count"] == 1
    products = client.get("/api/products").json()
    assert {product["CRM_Product_Code"] for product in products} == {"LOAD-P1", "LOAD-P3"}


def test_data_load_replace_blocks_removing_referenced_records(client) -> None:
    customer_id = _create_customer(client, "CUST-LOAD-LINKED")
    campaign_id = _create_campaign(client, "CMP-LOAD-LINKED")
    _create_lead(client, customer_id, campaign_id)
    payload = {
        "dataset_name": "customers",
        "file_name": "customers.json",
        "file_format": "json",
        "content": '[{"external_customer_id":"CUST-LOAD-OTHER","first_name":"Other"}]',
    }
    preview = client.post("/api/data/load/preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["replace_blocked_count"] > 0

    response = client.post("/api/data/load/apply", json={**payload, "mode": "replace"})
    assert response.status_code == 409


def test_data_load_preview_reports_invalid_relationships(client) -> None:
    payload = {
        "dataset_name": "leads",
        "file_name": "leads.csv",
        "file_format": "csv",
        "content": "customer_id\n999999\n",
    }
    preview = client.post("/api/data/load/preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["invalid_count"] == 1
    assert any(
        "referenced customers record not found" in issue
        for issue in preview.json()["preview_rows"][0]["issues"]
    )

    applied = client.post("/api/data/load/apply", json={**payload, "mode": "merge"})
    assert applied.status_code == 400


def _pipeline_workbook_payload(rows: list[dict[str, object]]) -> dict[str, str]:
    headers = list(dict.fromkeys(
        (
            *LEAD_COLUMNS,
            *CUSTOMER_COLUMNS,
            *PRODUCT_COLUMNS,
            *CAMPAIGN_COLUMNS,
            *MESSAGE_COLUMNS,
            *CALL_COLUMNS,
            *WEB_COLUMNS,
            *EVENT_COLUMNS,
            *TARGET_COLUMNS,
        )
    ))
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "dataset"
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    contents = BytesIO()
    workbook.save(contents)
    return {
        "file_name": "pipeline-test.xlsx",
        "content_base64": base64.b64encode(contents.getvalue()).decode("ascii"),
    }


def _pipeline_row(customer_id: str, suffix: str) -> dict[str, object]:
    return {
        "Customer_ID": customer_id,
        "CRM_Channel": "INHOUSE_ONLINE",
        "CRM_Product_Code": f"XLSX-PRODUCT-{suffix}",
        "CRM_Product_Name": f"Workbook Product {suffix}",
        "CRM_UTM_Campaign": f"XLSX-CAMPAIGN-{suffix}",
        "CRM_Gender": "female",
        "CRM_Age_Band": "26-35",
        "Label_Source_Disposition": "Just Browsing",
        "Label_Source_Lead_Status": "Contactable",
        "CDR_Total_Calls": 1,
        "CDR_Connected_Calls": 1,
        "CDR_Avg_Talk_Sec": 60,
    }


def test_pipeline_workbook_preview_and_merge_create_linked_records(client) -> None:
    payload = _pipeline_workbook_payload(
        [_pipeline_row("XLSX-CUSTOMER-001", "001"), _pipeline_row("XLSX-CUSTOMER-002", "002")]
    )
    preview = client.post("/api/data/load/pipeline/preview", json=payload)
    assert preview.status_code == 200, preview.text
    result = preview.json()
    assert result["row_count"] == 2
    assert result["invalid_count"] == 0
    assert result["quality"]["inspected_rows"] == 2
    assert result["quality"]["valid_rows"] == 2
    quality_fields = {field["field"]: field for field in result["quality"]["field_completeness"]}
    assert quality_fields["Customer_ID"] == {
        "field": "Customer_ID",
        "populated_count": 2,
        "missing_count": 0,
        "completeness": 1.0,
    }
    assert quality_fields["CRM_Tobacco_User"]["missing_count"] == 2
    assert len(result["preview_rows"]) == 2
    assert result["preview_rows"][0]["details"]["product"] == "Workbook Product 001"
    effects = {effect["dataset_name"]: effect for effect in result["effects"]}
    assert effects["customers"]["insert_count"] == 2
    assert effects["leads"]["insert_count"] == 2
    assert effects["tasks"]["insert_count"] == 2
    assert effects["calls"]["insert_count"] == 2

    applied = client.post(
        "/api/data/load/pipeline/apply",
        json={**payload, "mode": "merge"},
    )
    assert applied.status_code == 201, applied.text
    applied_effects = {effect["dataset_name"]: effect for effect in applied.json()["effects"]}
    assert applied_effects["customers"]["insert_count"] == 2
    assert applied_effects["leads"]["insert_count"] == 2
    assert applied_effects["lead_assignments"]["insert_count"] == 2
    assert applied_effects["lead_timeline_events"]["insert_count"] == 2
    assert applied_effects["engagement_events"]["insert_count"] == 2
    assert applied_effects["website_events"]["insert_count"] == 2
    assert applied_effects["tasks"]["insert_count"] == 2
    assert applied_effects["followups"]["insert_count"] == 2
    assert applied_effects["calls"]["insert_count"] == 2
    assert applied.json()["job"]["details"]["file_format"] == "xlsx"

    quality = client.get("/api/data/quality").json()
    for table in ("tasks", "followups", "lead_assignments", "lead_timeline_events"):
        assert quality["table_counts"][table] == 2
    assert quality["completeness"]["customers_with_external_id_ratio"] == 1.0


def test_pipeline_workbook_append_is_idempotent_and_invalid_rows_do_not_apply(client) -> None:
    payload = _pipeline_workbook_payload([_pipeline_row("XLSX-CUSTOMER-APPEND", "APPEND")])
    first = client.post("/api/data/load/pipeline/apply", json={**payload, "mode": "merge"})
    assert first.status_code == 201, first.text

    preview = client.post("/api/data/load/pipeline/preview", json=payload)
    assert preview.status_code == 200, preview.text
    assert preview.json()["preview_rows"][0]["action"] == "update", preview.json()
    assert {effect["dataset_name"]: effect for effect in preview.json()["effects"]}["leads"]["insert_count"] == 0

    appended = client.post("/api/data/load/pipeline/apply", json={**payload, "mode": "append"})
    assert appended.status_code == 201, appended.text
    append_effects = {effect["dataset_name"]: effect for effect in appended.json()["effects"]}
    assert append_effects["leads"]["skip_count"] == 1
    assert append_effects["leads"]["insert_count"] == 0

    invalid_payload = _pipeline_workbook_payload([_pipeline_row("", "INVALID")])
    invalid_preview = client.post("/api/data/load/pipeline/preview", json=invalid_payload)
    assert invalid_preview.status_code == 200
    assert invalid_preview.json()["invalid_count"] == 1
    assert invalid_preview.json()["quality"]["invalid_rows"] == 1
    invalid_apply = client.post(
        "/api/data/load/pipeline/apply",
        json={**invalid_payload, "mode": "merge"},
    )
    assert invalid_apply.status_code == 400
