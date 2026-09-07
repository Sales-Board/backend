from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.ai_prediction import AIPrediction
from app.models.call import Call
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.decision_recommendation import DecisionRecommendation
from app.models.engagement_event import EngagementEvent
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.lead_assignment import LeadAssignment
from app.models.lead_outcome import LeadOutcome
from app.models.lead_timeline_event import LeadTimelineEvent
from app.models.task import Task
from app.models.website_event import WebsiteEvent


class LifecycleRepository:
    def get_lead(self, db: Session, lead_id: int) -> Lead | None:
        return db.get(Lead, lead_id)

    def get_customer(self, db: Session, customer_id: int) -> Customer | None:
        return db.get(Customer, customer_id)

    def get_campaign(self, db: Session, campaign_id: int) -> Campaign | None:
        return db.get(Campaign, campaign_id)

    def get_decision(self, db: Session, decision_id: int) -> DecisionRecommendation | None:
        return db.get(DecisionRecommendation, decision_id)

    def get_current_assignment(self, db: Session, lead_id: int) -> LeadAssignment | None:
        stmt = (
            select(LeadAssignment)
            .where(LeadAssignment.lead_id == lead_id, LeadAssignment.is_current.is_(True))
            .order_by(LeadAssignment.id.desc())
            .limit(1)
        )
        return db.scalars(stmt).first()

    def list_assignments(self, db: Session, lead_id: int) -> list[LeadAssignment]:
        stmt = select(LeadAssignment).where(LeadAssignment.lead_id == lead_id).order_by(LeadAssignment.id.desc())
        return list(db.scalars(stmt).all())

    def create_assignment(
        self,
        db: Session,
        lead_id: int,
        customer_id: int | None,
        assignment_type: str,
        from_section: str | None,
        to_section: str | None,
        from_handler: str | None,
        to_handler: str | None,
        reason: str | None,
        trigger: str | None,
        related_decision_id: int | None,
        details: dict | None,
    ) -> LeadAssignment:
        db.execute(
            update(LeadAssignment)
            .where(LeadAssignment.lead_id == lead_id, LeadAssignment.is_current.is_(True))
            .values(is_current=False)
        )
        row = LeadAssignment(
            lead_id=lead_id,
            customer_id=customer_id,
            assignment_type=assignment_type,
            from_section=from_section,
            to_section=to_section,
            from_handler=from_handler,
            to_handler=to_handler,
            reason=reason,
            trigger=trigger,
            related_decision_id=related_decision_id,
            details=details,
            is_current=True,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def create_timeline_event(
        self,
        db: Session,
        lead_id: int,
        customer_id: int | None,
        event_type: str,
        event_source: str,
        details: dict | None,
    ) -> LeadTimelineEvent:
        row = LeadTimelineEvent(
            lead_id=lead_id,
            customer_id=customer_id,
            event_type=event_type,
            event_source=event_source,
            details=details,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_timeline(self, db: Session, lead_id: int, limit: int = 500) -> list[LeadTimelineEvent]:
        stmt = (
            select(LeadTimelineEvent)
            .where(LeadTimelineEvent.lead_id == lead_id)
            .order_by(LeadTimelineEvent.created_at.asc(), LeadTimelineEvent.id.asc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def create_outcome(
        self,
        db: Session,
        lead_id: int,
        customer_id: int | None,
        action_type: str,
        outcome_code: str,
        outcome_label: str | None,
        notes: str | None,
        followup_required: bool,
        next_action_hint: str | None,
        metadata: dict | None,
    ) -> LeadOutcome:
        row = LeadOutcome(
            lead_id=lead_id,
            customer_id=customer_id,
            action_type=action_type,
            outcome_code=outcome_code,
            outcome_label=outcome_label,
            notes=notes,
            followup_required=followup_required,
            next_action_hint=next_action_hint,
            metadata=metadata,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_outcomes(self, db: Session, lead_id: int, limit: int = 200) -> list[LeadOutcome]:
        stmt = select(LeadOutcome).where(LeadOutcome.lead_id == lead_id).order_by(LeadOutcome.id.desc()).limit(limit)
        return list(db.scalars(stmt).all())

    def update_lead_state(
        self,
        db: Session,
        lead: Lead,
        *,
        status: str | None = None,
        current_stage: str | None = None,
        current_section: str | None = None,
        current_handler: str | None = None,
        recommended_action: str | None = None,
    ) -> Lead:
        if status is not None:
            lead.status = status
        if current_stage is not None:
            lead.current_stage = current_stage
        if current_section is not None:
            lead.current_section = current_section
        if current_handler is not None:
            lead.current_handler = current_handler
        if recommended_action is not None:
            lead.recommended_action = recommended_action
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    def list_calls(self, db: Session, lead_id: int) -> list[Call]:
        stmt = select(Call).where(Call.lead_id == lead_id).order_by(Call.id.desc())
        return list(db.scalars(stmt).all())

    def list_tasks(self, db: Session, lead_id: int) -> list[Task]:
        stmt = select(Task).where(Task.lead_id == lead_id).order_by(Task.id.desc())
        return list(db.scalars(stmt).all())

    def list_followups(self, db: Session, lead_id: int) -> list[Followup]:
        stmt = select(Followup).where(Followup.lead_id == lead_id).order_by(Followup.id.desc())
        return list(db.scalars(stmt).all())

    def list_journey(self, db: Session, lead_id: int) -> list[WebsiteEvent]:
        stmt = select(WebsiteEvent).where(WebsiteEvent.lead_id == lead_id).order_by(WebsiteEvent.event_time.asc(), WebsiteEvent.id.asc())
        return list(db.scalars(stmt).all())

    def engagement_summary(self, db: Session, lead_id: int) -> dict:
        by_channel_stmt = (
            select(EngagementEvent.channel, func.count(EngagementEvent.id), func.coalesce(func.sum(EngagementEvent.metric_value), 0))
            .where(EngagementEvent.lead_id == lead_id)
            .group_by(EngagementEvent.channel)
        )
        summary: dict[str, dict[str, int]] = {}
        total_events = 0
        total_metric_value = 0
        for channel, count_value, metric_sum in db.execute(by_channel_stmt).all():
            count_int = int(count_value or 0)
            metric_int = int(metric_sum or 0)
            summary[channel or "unknown"] = {
                "events": count_int,
                "metric_sum": metric_int,
            }
            total_events += count_int
            total_metric_value += metric_int
        return {
            "total_events": total_events,
            "total_metric_value": total_metric_value,
            "by_channel": summary,
        }

    def latest_predictions_by_type(self, db: Session, lead_id: int) -> dict[str, AIPrediction]:
        rows = self.list_predictions(db, lead_id)
        latest: dict[str, AIPrediction] = {}
        for row in rows:
            if row.prediction_type not in latest:
                latest[row.prediction_type] = row
        return latest

    def list_predictions(self, db: Session, lead_id: int, limit: int = 200) -> list[AIPrediction]:
        stmt = select(AIPrediction).where(AIPrediction.lead_id == lead_id).order_by(AIPrediction.id.desc()).limit(limit)
        return list(db.scalars(stmt).all())

    def list_decisions(self, db: Session, lead_id: int, limit: int = 200) -> list[DecisionRecommendation]:
        stmt = (
            select(DecisionRecommendation)
            .where(DecisionRecommendation.lead_id == lead_id)
            .order_by(DecisionRecommendation.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
