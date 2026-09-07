from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DecisionRequest(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)


class DecisionResponse(BaseModel):
    decision_type: str
    recommended_action: str
    priority: str
    confidence: float
    rationale: str
    inputs: dict | None = None


class DecisionLogRead(BaseModel):
    id: int
    lead_id: int | None
    customer_id: int | None
    decision_type: str
    recommended_action: str
    priority: str
    confidence: float
    rationale: str
    inputs: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
