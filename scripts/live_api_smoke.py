#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


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
    call("GET", "/health")
    call("GET", "/api/health")
    call("GET", "/api/dashboard")

    customers = call("GET", "/api/customers")
    products = call("GET", "/api/products")
    campaigns = call("GET", "/api/campaigns")
    leads = call("GET", "/api/leads")
    tasks = call("GET", "/api/tasks")
    followups = call("GET", "/api/followups")
    calls = call("GET", "/api/calls")

    if not customers or not products or not campaigns or not leads or not tasks:
        print("Real dataset not loaded. Run ./scripts/preload_sample_data.py --reset first.")
        raise SystemExit(1)

    customer_id = int(customers[0]["id"])
    product_id = int(products[0]["id"])
    campaign_id = int(campaigns[0]["id"])
    lead_id = int(leads[0]["id"])
    task_id = int(tasks[0]["id"])
    call_id = int(calls[0]["id"]) if calls else None

    call("GET", f"/api/customers/{customer_id}")
    call("GET", f"/api/products/{product_id}")
    call("GET", f"/api/campaigns/{campaign_id}")
    call("GET", f"/api/campaigns/{campaign_id}/leads")
    call("GET", f"/api/campaigns/{campaign_id}/performance")

    call("GET", f"/api/leads/{lead_id}")
    call("GET", f"/api/leads/{lead_id}/journey")
    call("GET", f"/api/leads/{lead_id}/calls")
    timeline = call("GET", f"/api/leads/{lead_id}/timeline")
    details = call("GET", f"/api/leads/{lead_id}/details")
    call(
        "POST",
        f"/api/leads/{lead_id}/assign",
        payload={"to_section": "ai_qualification", "to_handler": "ai-agent", "reason": "smoke-assign"},
    )
    call(
        "POST",
        f"/api/leads/{lead_id}/transfer",
        payload={"to_section": "sales", "to_handler": "agent-101", "reason": "smoke-transfer"},
    )
    call(
        "POST",
        f"/api/leads/{lead_id}/outcomes",
        payload={
            "action_type": "human_call",
            "outcome_code": "interested",
            "outcome_label": "Interested",
            "followup_required": True,
            "next_action_hint": "call",
            "details": {"source": "live_api_smoke"},
        },
        expect=(201,),
    )
    outcomes = call("GET", f"/api/leads/{lead_id}/outcomes")

    required_detail_keys = {
        "lead",
        "customer",
        "campaign",
        "engagement",
        "journey",
        "ai",
        "calls",
        "tasks",
        "followups",
        "outcomes",
        "timeline",
    }
    if not isinstance(details, dict) or not required_detail_keys.issubset(details.keys()):
        print("Lifecycle details payload missing required keys")
        raise SystemExit(1)

    if not isinstance(timeline, list) or not isinstance(outcomes, list):
        print("Lifecycle timeline/outcomes payload shape is invalid")
        raise SystemExit(1)

    call("GET", f"/api/tasks/{task_id}")
    if followups:
        followup_id = int(followups[0]["id"])
        call("PATCH", f"/api/followups/{followup_id}", payload={"status": "completed"})

    if call_id is not None:
        call("GET", f"/api/calls/{call_id}")

    call("GET", "/api/journey/website")
    call("GET", f"/api/journey/leads/{lead_id}")

    call("GET", "/api/engagement/whatsapp")
    call("GET", "/api/engagement/rcs")
    call("GET", "/api/engagement/email")
    call("GET", "/api/engagement/website")

    train = call("POST", "/api/ml/train", payload={"model_name": "lead_conversion_real_data"}, expect=(201,))
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

    import_job = call(
        "POST",
        "/api/data/import",
        payload={
            "source_path": "/home/pavan/Desktop/FInal_year/sample_data/policy_indexed.json",
            "dataset_name": "policy_indexed",
            "file_format": "json",
        },
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
