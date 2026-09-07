from collections import defaultdict

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.task import Task


class ReportRepository:
    def fetch_campaign_performance(self, db: Session) -> list[dict[str, int | str | float]]:
        converted_case = case((Lead.status == "converted", 1), else_=0)
        stmt = (
            select(
                Campaign.id,
                Campaign.code,
                Campaign.name,
                func.count(Lead.id),
                func.coalesce(func.sum(converted_case), 0),
            )
            .outerjoin(Lead, Lead.campaign_id == Campaign.id)
            .group_by(Campaign.id, Campaign.code, Campaign.name)
            .order_by(Campaign.id)
        )

        items: list[dict[str, int | str | float]] = []
        for campaign_id, code, name, lead_count, converted_count in db.execute(stmt).all():
            leads = int(lead_count or 0)
            converted = int(converted_count or 0)
            conversion_rate = round((converted / leads), 4) if leads > 0 else 0.0
            items.append(
                {
                    "campaign_id": int(campaign_id),
                    "campaign_code": str(code),
                    "campaign_name": str(name),
                    "lead_count": leads,
                    "converted_leads": converted,
                    "conversion_rate": conversion_rate,
                }
            )
        return items

    def fetch_workload(self, db: Session) -> dict[str, int]:
        task_stmt = select(Task.status, func.count()).group_by(Task.status)
        followup_stmt = select(Followup.status, func.count()).group_by(Followup.status)

        task_counts: dict[str, int] = defaultdict(int)
        for status_value, count_value in db.execute(task_stmt).all():
            task_counts[(status_value or "unknown").lower()] += int(count_value)

        followup_counts: dict[str, int] = defaultdict(int)
        for status_value, count_value in db.execute(followup_stmt).all():
            followup_counts[(status_value or "unknown").lower()] += int(count_value)

        return {
            "total_tasks": sum(task_counts.values()),
            "open_tasks": task_counts.get("open", 0),
            "in_progress_tasks": task_counts.get("in_progress", 0),
            "completed_tasks": task_counts.get("completed", 0),
            "total_followups": sum(followup_counts.values()),
            "pending_followups": followup_counts.get("pending", 0) + followup_counts.get("scheduled", 0),
            "completed_followups": followup_counts.get("completed", 0),
        }

    def fetch_pipeline(self, db: Session) -> dict[str, int]:
        stmt = select(Lead.status, func.count()).group_by(Lead.status)
        counts: dict[str, int] = defaultdict(int)
        for status_value, count_value in db.execute(stmt).all():
            counts[(status_value or "unknown").lower()] += int(count_value)

        return {
            "total_leads": sum(counts.values()),
            "new_leads": counts.get("new", 0),
            "qualified_leads": counts.get("qualified", 0),
            "converted_leads": counts.get("converted", 0),
            "lost_leads": counts.get("lost", 0),
        }
