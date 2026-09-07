#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.database import get_session_factory
from app.models.call import Call
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.engagement_event import EngagementEvent
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.product import Product
from app.models.task import Task
from app.models.website_event import WebsiteEvent

DATASET_PATH = ROOT_DIR.parent / "sample_data" / "policy_indexed.json"


def _slug(value: str, max_len: int = 40) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:max_len] or "x"


def _channel_and_status(doc_type: str) -> tuple[str, str, str]:
    mapping = {
        "policy_document": ("website", "converted", "high"),
        "brochure": ("email", "qualified", "medium"),
        "cis": ("whatsapp", "new", "medium"),
    }
    return mapping.get(doc_type, ("website", "new", "low"))


def _reset_domain_tables(db: Session) -> None:
    from app.models.ai_prediction import AIPrediction
    from app.models.decision_recommendation import DecisionRecommendation

    for model in [
        Followup,
        Task,
        DecisionRecommendation,
        AIPrediction,
        Call,
        WebsiteEvent,
        EngagementEvent,
        Lead,
        Campaign,
        Product,
        Customer,
    ]:
        db.query(model).delete()
    db.flush()


def _remove_smoke_records(db: Session) -> None:
    db.query(Customer).filter(Customer.external_customer_id.like("SMOKE-%")).delete(synchronize_session=False)
    db.query(Customer).filter(Customer.external_customer_id.like("SAMPLE-%")).delete(synchronize_session=False)
    db.query(Campaign).filter(Campaign.code.like("SMOKE-%")).delete(synchronize_session=False)
    db.query(Campaign).filter(Campaign.code.like("SAMPLE-%")).delete(synchronize_session=False)
    db.query(Product).filter(Product.code.like("SMOKE-%")).delete(synchronize_session=False)
    db.query(Product).filter(Product.code.like("SAMPLE-%")).delete(synchronize_session=False)
    db.flush()


def _load_dataset() -> dict:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Sample dataset not found at: {DATASET_PATH}")
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _count(db: Session, model, *filters) -> int:
    stmt = select(func.count()).select_from(model)
    for rule in filters:
        stmt = stmt.where(rule)
    return int(db.scalar(stmt) or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load real sample_data records into PostgreSQL")
    parser.add_argument("--reset", action="store_true", help="Delete existing domain rows before load")
    parser.add_argument("--keep-smoke", action="store_true", help="Do not remove existing SMOKE/SAMPLE rows")
    args = parser.parse_args()

    session_factory = get_session_factory()
    if session_factory is None:
        raise RuntimeError("Database is not configured")

    dataset = _load_dataset()
    groups: dict = dataset.get("groups", {})

    created = {
        "products": 0,
        "campaigns": 0,
        "customers": 0,
        "leads": 0,
        "tasks": 0,
        "followups": 0,
        "calls": 0,
        "engagement_events": 0,
        "website_events": 0,
    }

    with session_factory() as db:
        if args.reset:
            _reset_domain_tables(db)
        elif not args.keep_smoke:
            _remove_smoke_records(db)

        for group_key, group_data in groups.items():
            product_name = str(group_data.get("product_name") or group_key.replace("_", " ")).strip()
            plan_categories = group_data.get("plan_categories") or []
            files = group_data.get("files") or []

            product_code = f"PRD-{_slug(group_key, 50)}"[:64]
            product = db.scalar(select(Product).where(Product.code == product_code))
            if product is None:
                product = Product(
                    code=product_code,
                    name=product_name[:150],
                    category=", ".join(plan_categories)[:100] if plan_categories else None,
                    is_active=True,
                )
                db.add(product)
                db.flush()
                created["products"] += 1

            campaign_code = f"CMP-{_slug(group_key, 50)}"[:64]
            campaign = db.scalar(select(Campaign).where(Campaign.code == campaign_code))
            if campaign is None:
                campaign = Campaign(
                    code=campaign_code,
                    name=product_name[:150],
                    channel="website",
                    status="active",
                )
                db.add(campaign)
                db.flush()
                created["campaigns"] += 1

            for file_data in files:
                doc_uid = str(file_data.get("doc_uid") or file_data.get("pdf_sha256") or "").strip()
                if not doc_uid:
                    continue
                external_id = doc_uid[:64]

                customer = db.scalar(select(Customer).where(Customer.external_customer_id == external_id))
                if customer is None:
                    customer = Customer(
                        external_customer_id=external_id,
                        first_name=str(file_data.get("title") or "Doc")[:100],
                        last_name=str(file_data.get("doc_type") or "Record")[:100],
                    )
                    db.add(customer)
                    db.flush()
                    created["customers"] += 1

                doc_type = str(file_data.get("doc_type") or "unknown").strip().lower()
                source_channel, status_value, priority = _channel_and_status(doc_type)

                lead = db.scalar(
                    select(Lead).where(
                        Lead.customer_id == customer.id,
                        Lead.campaign_id == campaign.id,
                        Lead.source_channel == source_channel,
                        Lead.source_medium == doc_type,
                    )
                )
                if lead is None:
                    lead = Lead(
                        customer_id=customer.id,
                        campaign_id=campaign.id,
                        source_channel=source_channel,
                        source_medium=doc_type,
                        status=status_value,
                        priority=priority,
                    )
                    db.add(lead)
                    db.flush()
                    created["leads"] += 1

                existing_event = db.scalar(select(EngagementEvent.id).where(EngagementEvent.lead_id == lead.id))
                if existing_event is None:
                    page_count = int(file_data.get("page_count") or 0)
                    db.add(
                        EngagementEvent(
                            lead_id=lead.id,
                            customer_id=customer.id,
                            campaign_id=campaign.id,
                            channel=source_channel,
                            metric_type="viewed",
                            metric_value=max(1, page_count),
                            event_payload={
                                "doc_type": doc_type,
                                "filename": file_data.get("filename"),
                                "display_ref": file_data.get("display_ref"),
                                "uin": file_data.get("uin") or [],
                            },
                        )
                    )
                    created["engagement_events"] += 1

                existing_web = db.scalar(select(WebsiteEvent.id).where(WebsiteEvent.lead_id == lead.id))
                if existing_web is None:
                    db.add(
                        WebsiteEvent(
                            lead_id=lead.id,
                            customer_id=customer.id,
                            event_name="document_indexed",
                            step_name=doc_type[:100],
                            step_number=1,
                            device_type="web",
                            is_repeat_visitor=False,
                            event_payload={"title": file_data.get("title"), "url": file_data.get("url")},
                        )
                    )
                    created["website_events"] += 1

                task_title = f"Review {str(file_data.get('title') or doc_type)[:120]}"
                task = db.scalar(select(Task).where(Task.lead_id == lead.id, Task.title == task_title))
                if task is None:
                    due_at = datetime.now(UTC) + timedelta(days=3)
                    task = Task(
                        lead_id=lead.id,
                        customer_id=customer.id,
                        title=task_title,
                        description=str(file_data.get("display_ref") or "Policy document review")[:1000],
                        status="open" if doc_type != "policy_document" else "completed",
                        priority=priority,
                        due_at=due_at,
                    )
                    db.add(task)
                    db.flush()
                    created["tasks"] += 1

                followup = db.scalar(select(Followup).where(Followup.task_id == task.id))
                if followup is None:
                    followup = Followup(
                        task_id=task.id,
                        lead_id=lead.id,
                        customer_id=customer.id,
                        channel="call" if doc_type == "policy_document" else "email",
                        notes=str(file_data.get("display_ref") or "sample-data followup")[:1000],
                        status="completed" if doc_type == "policy_document" else "pending",
                        scheduled_at=datetime.now(UTC) + timedelta(days=1),
                        completed_at=datetime.now(UTC) if doc_type == "policy_document" else None,
                    )
                    db.add(followup)
                    created["followups"] += 1

                if doc_type == "policy_document":
                    call = db.scalar(select(Call).where(Call.lead_id == lead.id, Call.customer_id == customer.id))
                    if call is None:
                        started = datetime.now(UTC) - timedelta(minutes=8)
                        ended = datetime.now(UTC) - timedelta(minutes=2)
                        db.add(
                            Call(
                                lead_id=lead.id,
                                customer_id=customer.id,
                                direction="outbound",
                                status="completed",
                                phone_number=None,
                                notes="Policy document consultation",
                                started_at=started,
                                ended_at=ended,
                                duration_seconds=max(0, int((ended - started).total_seconds())),
                            )
                        )
                        created["calls"] += 1

        db.commit()

        total_records = {
            "products": _count(db, Product),
            "campaigns": _count(db, Campaign),
            "customers": _count(db, Customer),
            "leads": _count(db, Lead),
            "tasks": _count(db, Task),
            "followups": _count(db, Followup),
            "calls": _count(db, Call),
            "engagement_events": _count(db, EngagementEvent),
            "website_events": _count(db, WebsiteEvent),
        }

    print("real-sample-data-ready")
    print(f"dataset_path: {DATASET_PATH}")
    print("new_rows:")
    for key, value in created.items():
        print(f"  {key}: {value}")
    print("total_rows:")
    for key, value in total_records.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
