from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.call import Call
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.engagement_event import EngagementEvent
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.task import Task


class AnalyticsRepository:
    @staticmethod
    def _count(db: Session, model: type) -> int:
        stmt = select(func.count()).select_from(model)
        return int(db.scalar(stmt) or 0)

    def fetch_overview(self, db: Session) -> dict[str, int]:
        total_customers = self._count(db, Customer)
        total_leads = self._count(db, Lead)
        total_campaigns = self._count(db, Campaign)
        total_calls = self._count(db, Call)

        open_tasks_stmt = select(func.count()).select_from(Task).where(Task.status.in_(["open", "in_progress"]))
        pending_followups_stmt = (
            select(func.count())
            .select_from(Followup)
            .where(Followup.status.in_(["pending", "scheduled"]))
        )
        converted_stmt = select(func.count()).select_from(Lead).where(Lead.status == "converted")

        return {
            "total_customers": total_customers,
            "total_leads": total_leads,
            "total_campaigns": total_campaigns,
            "total_calls": total_calls,
            "open_tasks": int(db.scalar(open_tasks_stmt) or 0),
            "pending_followups": int(db.scalar(pending_followups_stmt) or 0),
            "converted_leads": int(db.scalar(converted_stmt) or 0),
        }

    def fetch_funnel_status_counts(self, db: Session) -> dict[str, int]:
        stmt = select(Lead.status, func.count()).group_by(Lead.status)
        rows = db.execute(stmt).all()
        result: dict[str, int] = defaultdict(int)
        for status_value, count_value in rows:
            key = (status_value or "unknown").lower()
            result[key] += int(count_value)
        return dict(result)

    def fetch_channel_analytics(self, db: Session) -> list[dict[str, int | str]]:
        lead_stmt = select(Lead.source_channel, func.count()).group_by(Lead.source_channel)
        engagement_stmt = (
            select(EngagementEvent.channel, func.coalesce(func.sum(EngagementEvent.metric_value), 0))
            .group_by(EngagementEvent.channel)
        )

        lead_map: dict[str, int] = {}
        for channel, count_value in db.execute(lead_stmt).all():
            lead_map[(channel or "unknown").lower()] = int(count_value)

        engagement_map: dict[str, int] = {}
        for channel, count_value in db.execute(engagement_stmt).all():
            engagement_map[(channel or "unknown").lower()] = int(count_value)

        channels = sorted(set(lead_map.keys()) | set(engagement_map.keys()))
        return [
            {
                "channel": channel,
                "lead_count": lead_map.get(channel, 0),
                "engagement_events": engagement_map.get(channel, 0),
            }
            for channel in channels
        ]
