#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from sqlalchemy import select

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


def _get_or_create_customer(db, external_customer_id: str, first_name: str) -> Customer:
    row = db.scalar(select(Customer).where(Customer.external_customer_id == external_customer_id))
    if row is not None:
        return row
    row = Customer(external_customer_id=external_customer_id, first_name=first_name)
    db.add(row)
    db.flush()
    return row


def _get_or_create_campaign(db, code: str, name: str, channel: str) -> Campaign:
    row = db.scalar(select(Campaign).where(Campaign.code == code))
    if row is not None:
        return row
    row = Campaign(code=code, name=name, channel=channel, status="active")
    db.add(row)
    db.flush()
    return row


def _get_or_create_product(db, code: str, name: str) -> Product:
    row = db.scalar(select(Product).where(Product.code == code))
    if row is not None:
        return row
    row = Product(code=code, name=name, category="insurance", is_active=True)
    db.add(row)
    db.flush()
    return row


def _get_or_create_lead(db, customer_id: int, campaign_id: int, source_channel: str, status_value: str, priority: str) -> Lead:
    row = db.scalar(
        select(Lead).where(
            Lead.customer_id == customer_id,
            Lead.campaign_id == campaign_id,
            Lead.source_channel == source_channel,
            Lead.status == status_value,
        )
    )
    if row is not None:
        return row
    row = Lead(
        customer_id=customer_id,
        campaign_id=campaign_id,
        source_channel=source_channel,
        status=status_value,
        priority=priority,
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_task(db, lead_id: int, customer_id: int, title: str, status_value: str, priority: str) -> Task:
    row = db.scalar(select(Task).where(Task.lead_id == lead_id, Task.title == title))
    if row is not None:
        return row
    row = Task(
        lead_id=lead_id,
        customer_id=customer_id,
        title=title,
        description="Seeded sample task",
        status=status_value,
        priority=priority,
        due_at=datetime.now(UTC) + timedelta(days=2),
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_followup(db, task_id: int, lead_id: int, customer_id: int, channel: str, status_value: str) -> Followup:
    row = db.scalar(select(Followup).where(Followup.task_id == task_id, Followup.channel == channel))
    if row is not None:
        return row
    row = Followup(
        task_id=task_id,
        lead_id=lead_id,
        customer_id=customer_id,
        channel=channel,
        status=status_value,
        notes="Seeded follow-up",
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        completed_at=datetime.now(UTC) if status_value == "completed" else None,
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_call(db, lead_id: int, customer_id: int, phone_number: str, status_value: str) -> Call:
    row = db.scalar(select(Call).where(Call.lead_id == lead_id, Call.phone_number == phone_number))
    if row is not None:
        return row
    started = datetime.now(UTC) - timedelta(minutes=5)
    ended = datetime.now(UTC) - timedelta(minutes=2)
    row = Call(
        lead_id=lead_id,
        customer_id=customer_id,
        direction="outbound",
        status=status_value,
        phone_number=phone_number,
        started_at=started,
        ended_at=ended,
        duration_seconds=max(0, int((ended - started).total_seconds())),
        notes="Seeded call",
    )
    db.add(row)
    db.flush()
    return row


def _seed_engagement_events(db, lead_id: int, customer_id: int, campaign_id: int) -> int:
    existing = db.scalar(select(EngagementEvent).where(EngagementEvent.lead_id == lead_id))
    if existing is not None:
        return 0

    rows = [
        EngagementEvent(
            lead_id=lead_id,
            customer_id=customer_id,
            campaign_id=campaign_id,
            channel="email",
            metric_type="sent",
            metric_value=2,
        ),
        EngagementEvent(
            lead_id=lead_id,
            customer_id=customer_id,
            campaign_id=campaign_id,
            channel="whatsapp",
            metric_type="clicked",
            metric_value=1,
        ),
        EngagementEvent(
            lead_id=lead_id,
            customer_id=customer_id,
            campaign_id=campaign_id,
            channel="website",
            metric_type="viewed",
            metric_value=3,
        ),
    ]
    db.add_all(rows)
    db.flush()
    return len(rows)


def _seed_website_events(db, lead_id: int, customer_id: int) -> int:
    existing = db.scalar(select(WebsiteEvent).where(WebsiteEvent.lead_id == lead_id))
    if existing is not None:
        return 0

    rows = [
        WebsiteEvent(
            lead_id=lead_id,
            customer_id=customer_id,
            event_name="page_view",
            step_name="landing",
            step_number=1,
            device_type="mobile",
            is_repeat_visitor=False,
            event_payload={"path": "/"},
        ),
        WebsiteEvent(
            lead_id=lead_id,
            customer_id=customer_id,
            event_name="cta_click",
            step_name="quote_start",
            step_number=2,
            device_type="mobile",
            is_repeat_visitor=True,
            event_payload={"button": "start_quote"},
        ),
    ]
    db.add_all(rows)
    db.flush()
    return len(rows)


def main() -> None:
    session_factory = get_session_factory()
    if session_factory is None:
        raise RuntimeError("Database is not configured")

    created = {
        "customers": 0,
        "campaigns": 0,
        "products": 0,
        "leads": 0,
        "tasks": 0,
        "followups": 0,
        "calls": 0,
        "engagement_events": 0,
        "website_events": 0,
    }

    with session_factory() as db:
        c1 = _get_or_create_customer(db, "SAMPLE-CUST-001", "Asha")
        c2 = _get_or_create_customer(db, "SAMPLE-CUST-002", "Ravi")
        c3 = _get_or_create_customer(db, "SAMPLE-CUST-003", "Neha")

        camp_email = _get_or_create_campaign(db, "SAMPLE-CMP-EMAIL", "Email Growth", "email")
        camp_web = _get_or_create_campaign(db, "SAMPLE-CMP-WEB", "Website Conversions", "website")

        _get_or_create_product(db, "SAMPLE-PROD-TERM", "Term Protect")
        _get_or_create_product(db, "SAMPLE-PROD-WEALTH", "Wealth Builder")

        leads = [
            _get_or_create_lead(db, c1.id, camp_email.id, "email", "new", "medium"),
            _get_or_create_lead(db, c2.id, camp_email.id, "email", "qualified", "high"),
            _get_or_create_lead(db, c3.id, camp_web.id, "website", "converted", "high"),
            _get_or_create_lead(db, c1.id, camp_web.id, "website", "lost", "low"),
        ]

        t1 = _get_or_create_task(db, leads[0].id, c1.id, "Call back prospect", "open", "high")
        t2 = _get_or_create_task(db, leads[1].id, c2.id, "Share brochure", "in_progress", "medium")

        _get_or_create_followup(db, t1.id, leads[0].id, c1.id, "call", "pending")
        _get_or_create_followup(db, t2.id, leads[1].id, c2.id, "email", "completed")

        _get_or_create_call(db, leads[0].id, c1.id, "+910000001001", "completed")
        _get_or_create_call(db, leads[2].id, c3.id, "+910000001003", "completed")

        created["engagement_events"] += _seed_engagement_events(db, leads[0].id, c1.id, camp_email.id)
        created["engagement_events"] += _seed_engagement_events(db, leads[2].id, c3.id, camp_web.id)
        created["website_events"] += _seed_website_events(db, leads[0].id, c1.id)
        created["website_events"] += _seed_website_events(db, leads[2].id, c3.id)

        # Recompute counts quickly by checking sample identifiers.
        created["customers"] = int(
            db.scalar(select(func.count()).select_from(Customer).where(Customer.external_customer_id.like("SAMPLE-CUST-%")))
            or 0
        )
        created["campaigns"] = int(
            db.scalar(select(func.count()).select_from(Campaign).where(Campaign.code.like("SAMPLE-CMP-%"))) or 0
        )
        created["products"] = int(
            db.scalar(select(func.count()).select_from(Product).where(Product.code.like("SAMPLE-PROD-%"))) or 0
        )
        created["leads"] = len(leads)
        created["tasks"] = int(
            db.scalar(select(func.count()).select_from(Task).where(Task.title.in_(["Call back prospect", "Share brochure"])))
            or 0
        )
        created["followups"] = int(
            db.scalar(select(func.count()).select_from(Followup).where(Followup.notes == "Seeded follow-up")) or 0
        )
        created["calls"] = int(db.scalar(select(func.count()).select_from(Call).where(Call.notes == "Seeded call")) or 0)

        db.commit()

    print("sample-data-ready")
    for key, value in created.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
