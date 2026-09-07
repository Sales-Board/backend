#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def call(method: str, path: str, payload: dict | None = None, expect: tuple[int, ...] = (200,)) -> dict | list | None:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8")

    ok = status in expect
    print(f"{method} {path} -> {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        if body:
            print(body[:500])
        raise SystemExit(1)

    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def main() -> None:
    ts = int(time.time())

    call("GET", "/health")
    call("GET", "/api/health")
    call("GET", "/api/dashboard")

    customer = call(
        "POST",
        "/api/customers",
        payload={"external_customer_id": f"SMOKE-CUST-{ts}", "first_name": "Smoke"},
        expect=(201,),
    )
    customer_id = int(customer["id"])

    product = call(
        "POST",
        "/api/products",
        payload={"code": f"SMOKE-PROD-{ts}", "name": "Smoke Product", "category": "insurance", "status": "active"},
        expect=(201,),
    )
    product_id = int(product["id"])

    campaign = call(
        "POST",
        "/api/campaigns",
        payload={"code": f"SMOKE-CMP-{ts}", "name": "Smoke Campaign", "channel": "email", "status": "active"},
        expect=(201,),
    )
    campaign_id = int(campaign["id"])

    lead = call(
        "POST",
        "/api/leads",
        payload={
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "source_channel": "email",
            "status": "new",
            "priority": "high",
        },
        expect=(201,),
    )
    lead_id = int(lead["id"])

    task = call(
        "POST",
        "/api/tasks",
        payload={
            "lead_id": lead_id,
            "customer_id": customer_id,
            "title": "Smoke task",
            "status": "open",
            "priority": "high",
        },
        expect=(201,),
    )
    task_id = int(task["id"])

    followup = call(
        "POST",
        "/api/followups",
        payload={
            "task_id": task_id,
            "lead_id": lead_id,
            "customer_id": customer_id,
            "channel": "call",
            "status": "pending",
        },
        expect=(201,),
    )
    followup_id = int(followup["id"])

    call_entry = call(
        "POST",
        "/api/calls",
        payload={
            "lead_id": lead_id,
            "customer_id": customer_id,
            "direction": "outbound",
            "status": "scheduled",
            "phone_number": "+910000009999",
        },
        expect=(201,),
    )
    call_id = int(call_entry["id"])

    call("GET", "/api/customers")
    call("GET", f"/api/customers/{customer_id}")
    call("PATCH", f"/api/customers/{customer_id}", payload={"first_name": "SmokeUpdated"})

    call("GET", "/api/products")
    call("GET", f"/api/products/{product_id}")
    call("PATCH", f"/api/products/{product_id}", payload={"status": "inactive"})

    call("GET", "/api/campaigns")
    call("GET", f"/api/campaigns/{campaign_id}")
    call("PATCH", f"/api/campaigns/{campaign_id}", payload={"status": "paused"})
    call("GET", f"/api/campaigns/{campaign_id}/leads")
    call("GET", f"/api/campaigns/{campaign_id}/performance")

    call("GET", "/api/leads")
    call("GET", f"/api/leads/{lead_id}")
    call("PATCH", f"/api/leads/{lead_id}", payload={"status": "qualified"})
    call("GET", f"/api/leads/{lead_id}/journey")
    call("GET", f"/api/leads/{lead_id}/calls")

    call("GET", "/api/tasks")
    call("GET", f"/api/tasks/{task_id}")
    call("PATCH", f"/api/tasks/{task_id}", payload={"status": "in_progress"})

    call("GET", "/api/followups")
    call("PATCH", f"/api/followups/{followup_id}", payload={"status": "completed"})

    call("GET", "/api/calls")
    call("GET", f"/api/calls/{call_id}")
    call("PATCH", f"/api/calls/{call_id}", payload={"notes": "smoke"})
    call("POST", f"/api/calls/{call_id}/start", payload={})
    call("POST", f"/api/calls/{call_id}/end", payload={})

    call("GET", "/api/journey/website")
    call("GET", f"/api/journey/leads/{lead_id}")

    call("GET", "/api/engagement/whatsapp")
    call("GET", "/api/engagement/rcs")
    call("GET", "/api/engagement/email")
    call("GET", "/api/engagement/website")

    train = call("POST", "/api/ml/train", payload={"model_name": "lead_conversion_baseline"}, expect=(201,))
    train_id = int(train["id"])
    call("GET", f"/api/ml/train/{train_id}")
    call("GET", "/api/ml/models")

    for endpoint in [
        "validity",
        "intent",
        "conversion",
        "product-recommendation",
        "lead-score",
        "segment",
        "next-best-action",
    ]:
        call("POST", f"/api/ai/{endpoint}", payload={"lead_id": lead_id})

    call("POST", "/api/ai/analyze-lead", payload={"lead_id": lead_id})
    call("GET", f"/api/ai/leads/{lead_id}")
    call("GET", f"/api/ai/customers/{customer_id}")

    call("POST", "/api/decision/next-action", payload={"lead_id": lead_id})
    call("GET", f"/api/decision/leads/{lead_id}")
    call("GET", f"/api/decision/customers/{customer_id}")

    call("GET", "/api/analytics/overview")
    call("GET", "/api/analytics/funnel")
    call("GET", "/api/analytics/channels")

    call("GET", "/api/reports/campaign-performance")
    call("GET", "/api/reports/workload")
    call("GET", "/api/reports/pipeline")

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / "import_customers.csv"
        csv_path.write_text("external_customer_id,first_name\nTMP-1,Temp\n,Missing\n", encoding="utf-8")
        import_job = call(
            "POST",
            "/api/data/import",
            payload={"source_path": str(csv_path), "dataset_name": "customers", "file_format": "csv"},
            expect=(201,),
        )
        call("GET", f"/api/data/import/{int(import_job['id'])}")

    call("GET", "/api/data/quality")
    call("GET", "/api/data/validation")
    call("GET", "/api/data/history")
    call("POST", "/api/data/export", payload={"resource": "leads", "file_format": "json"}, expect=(201,))

    print("ALL_API_CHECKS_PASSED")


if __name__ == "__main__":
    main()
