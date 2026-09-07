from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ai import AIPredictionLogRead
from app.schemas.call import CallRead
from app.schemas.campaign import CampaignRead
from app.schemas.customer import CustomerRead
from app.schemas.decision import DecisionLogRead
from app.schemas.lead import LeadRead
from app.schemas.task_followup import FollowupRead, TaskRead
from app.schemas.website_journey import WebsiteEventRead


class LeadAssignmentRequest(BaseModel):
    to_section: str = Field(min_length=1, max_length=64)
    to_handler: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=255)
    trigger: str | None = Field(default="manual", max_length=64)
    related_decision_id: int | None = Field(default=None, ge=1)
    details: dict | None = None


class LeadAssignmentRead(BaseModel):
    id: int
    lead_id: int
    customer_id: int | None
    assignment_type: str
    from_section: str | None
    to_section: str | None
    from_handler: str | None
    to_handler: str | None
    reason: str | None
    trigger: str | None
    related_decision_id: int | None
    is_current: bool
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadOutcomeCreate(BaseModel):
    action_type: str = Field(default="unknown", min_length=1, max_length=32)
    outcome_code: str = Field(min_length=1, max_length=64)
    outcome_label: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    followup_required: bool = False
    next_action_hint: str | None = Field(default=None, max_length=64)
    metadata: dict | None = None


class LeadOutcomeRead(BaseModel):
    id: int
    lead_id: int
    customer_id: int | None
    action_type: str
    outcome_code: str
    outcome_label: str | None
    notes: str | None
    followup_required: bool
    next_action_hint: str | None
    metadata: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadTimelineEventRead(BaseModel):
    id: int
    lead_id: int
    customer_id: int | None
    event_type: str
    event_source: str
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadDetailsResponse(BaseModel):
    lead: LeadRead
    customer: CustomerRead | None
    campaign: CampaignRead | None
    assignment: LeadAssignmentRead | None
    engagement: dict
    journey: list[WebsiteEventRead]
    ai: dict
    calls: list[CallRead]
    tasks: list[TaskRead]
    followups: list[FollowupRead]
    outcomes: list[LeadOutcomeRead]
    timeline: list[LeadTimelineEventRead]
