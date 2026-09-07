from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.followup import Followup
from app.repositories.lifecycle_repository import LifecycleRepository
from app.schemas.ai import AIPredictionLogRead
from app.schemas.call import CallRead
from app.schemas.campaign import CampaignRead
from app.schemas.customer import CustomerRead
from app.schemas.decision import DecisionLogRead
from app.schemas.lifecycle import (
    LeadAssignmentRead,
    LeadAssignmentRequest,
    LeadDetailsResponse,
    LeadOutcomeCreate,
    LeadOutcomeRead,
    LeadTimelineEventRead,
)
from app.schemas.task_followup import FollowupRead, TaskRead
from app.schemas.website_journey import WebsiteEventRead


class LifecycleService:
    def __init__(self, repository: LifecycleRepository | None = None) -> None:
        self.repository = repository or LifecycleRepository()

    def add_timeline_event(
        self,
        db: Session,
        lead_id: int,
        customer_id: int | None,
        event_type: str,
        event_source: str = "system",
        details: dict | None = None,
    ) -> LeadTimelineEventRead:
        self._assert_lead_exists(db, lead_id)
        row = self.repository.create_timeline_event(
            db,
            lead_id=lead_id,
            customer_id=customer_id,
            event_type=event_type,
            event_source=event_source,
            details=details,
        )
        return LeadTimelineEventRead.model_validate(row)

    def list_timeline(self, db: Session, lead_id: int) -> list[LeadTimelineEventRead]:
        self._assert_lead_exists(db, lead_id)
        rows = self.repository.list_timeline(db, lead_id)
        return [LeadTimelineEventRead.model_validate(row) for row in rows]

    def assign_lead(self, db: Session, lead_id: int, payload: LeadAssignmentRequest) -> LeadAssignmentRead:
        lead = self._assert_lead_exists(db, lead_id)
        current = self.repository.get_current_assignment(db, lead_id)

        row = self.repository.create_assignment(
            db,
            lead_id=lead.id,
            customer_id=lead.customer_id,
            assignment_type="assign" if current is None else "transfer",
            from_section=current.to_section if current is not None else lead.current_section,
            to_section=payload.to_section,
            from_handler=current.to_handler if current is not None else lead.current_handler,
            to_handler=payload.to_handler,
            reason=payload.reason,
            trigger=payload.trigger,
            related_decision_id=payload.related_decision_id,
            details=payload.details,
        )

        self.repository.update_lead_state(
            db,
            lead,
            current_section=payload.to_section,
            current_handler=payload.to_handler,
            current_stage="assigned",
        )

        self.repository.create_timeline_event(
            db,
            lead_id=lead.id,
            customer_id=lead.customer_id,
            event_type="lead_assigned" if current is None else "lead_transferred",
            event_source="assignment_service",
            details={
                "from_section": row.from_section,
                "to_section": row.to_section,
                "from_handler": row.from_handler,
                "to_handler": row.to_handler,
                "reason": row.reason,
                "trigger": row.trigger,
                "related_decision_id": row.related_decision_id,
            },
        )

        return LeadAssignmentRead.model_validate(row)

    def record_outcome(self, db: Session, lead_id: int, payload: LeadOutcomeCreate) -> LeadOutcomeRead:
        lead = self._assert_lead_exists(db, lead_id)
        outcome_code = payload.outcome_code.lower()

        row = self.repository.create_outcome(
            db,
            lead_id=lead.id,
            customer_id=lead.customer_id,
            action_type=payload.action_type,
            outcome_code=payload.outcome_code,
            outcome_label=payload.outcome_label,
            notes=payload.notes,
            followup_required=payload.followup_required,
            next_action_hint=payload.next_action_hint,
            details=payload.details,
        )

        next_status = None
        next_stage = None
        if "convert" in outcome_code:
            next_status = "converted"
            next_stage = "completed"
        elif outcome_code in {"not_interested", "lost", "rejected"}:
            next_status = "lost"
            next_stage = "closed"
        elif outcome_code in {"interested", "callback", "follow_up"}:
            next_status = "qualified"
            next_stage = "nurturing"

        self.repository.update_lead_state(
            db,
            lead,
            status=next_status,
            current_stage=next_stage,
            recommended_action=payload.next_action_hint,
        )

        self.repository.create_timeline_event(
            db,
            lead_id=lead.id,
            customer_id=lead.customer_id,
            event_type="outcome_recorded",
            event_source="outcome_service",
            details={
                "action_type": payload.action_type,
                "outcome_code": payload.outcome_code,
                "outcome_label": payload.outcome_label,
                "followup_required": payload.followup_required,
                "next_action_hint": payload.next_action_hint,
            },
        )

        if payload.followup_required:
            followup = Followup(
                task_id=None,
                lead_id=lead.id,
                customer_id=lead.customer_id,
                channel=payload.next_action_hint or "call",
                notes=payload.notes or f"Follow-up required due to outcome {payload.outcome_code}",
                status="pending",
            )
            db.add(followup)
            db.commit()
            db.refresh(followup)

            self.repository.create_timeline_event(
                db,
                lead_id=lead.id,
                customer_id=lead.customer_id,
                event_type="followup_created",
                event_source="outcome_service",
                details={"followup_id": followup.id, "channel": followup.channel, "status": followup.status},
            )

        return LeadOutcomeRead.model_validate(row)

    def list_outcomes(self, db: Session, lead_id: int) -> list[LeadOutcomeRead]:
        self._assert_lead_exists(db, lead_id)
        rows = self.repository.list_outcomes(db, lead_id)
        return [LeadOutcomeRead.model_validate(row) for row in rows]

    def get_lead_details(self, db: Session, lead_id: int) -> LeadDetailsResponse:
        lead = self._assert_lead_exists(db, lead_id)
        customer = self.repository.get_customer(db, lead.customer_id)
        campaign = self.repository.get_campaign(db, lead.campaign_id) if lead.campaign_id is not None else None
        assignment = self.repository.get_current_assignment(db, lead_id)

        journey = self.repository.list_journey(db, lead_id)
        calls = self.repository.list_calls(db, lead_id)
        tasks = self.repository.list_tasks(db, lead_id)
        followups = self.repository.list_followups(db, lead_id)
        outcomes = self.repository.list_outcomes(db, lead_id)
        timeline = self.repository.list_timeline(db, lead_id)
        predictions = self.repository.list_predictions(db, lead_id)
        decisions = self.repository.list_decisions(db, lead_id)

        latest_predictions = self.repository.latest_predictions_by_type(db, lead_id)

        ai_block = {
            "latest": {k: AIPredictionLogRead.model_validate(v).model_dump() for k, v in latest_predictions.items()},
            "recent": [AIPredictionLogRead.model_validate(row).model_dump() for row in predictions],
            "recent_decisions": [DecisionLogRead.model_validate(row).model_dump() for row in decisions],
        }

        engagement = self.repository.engagement_summary(db, lead_id)

        return LeadDetailsResponse(
            lead=lead,
            customer=CustomerRead.model_validate(customer) if customer is not None else None,
            campaign=CampaignRead.model_validate(campaign) if campaign is not None else None,
            assignment=LeadAssignmentRead.model_validate(assignment) if assignment is not None else None,
            engagement=engagement,
            journey=[WebsiteEventRead.model_validate(item) for item in journey],
            ai=ai_block,
            calls=[CallRead.model_validate(item) for item in calls],
            tasks=[TaskRead.model_validate(item) for item in tasks],
            followups=[FollowupRead.model_validate(item) for item in followups],
            outcomes=[LeadOutcomeRead.model_validate(item) for item in outcomes],
            timeline=[LeadTimelineEventRead.model_validate(item) for item in timeline],
        )

    def _assert_lead_exists(self, db: Session, lead_id: int):
        lead = self.repository.get_lead(db, lead_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return lead
