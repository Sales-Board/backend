from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIPredictionRequest(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    context: dict | None = None


class AIPredictionResponse(BaseModel):
    prediction_type: str
    model_name: str
    score: float
    label: str
    rationale: str
    details: dict | None = None


class AIPredictionLogRead(BaseModel):
    id: int
    lead_id: int | None
    customer_id: int | None
    prediction_type: str
    model_name: str
    score: float
    label: str
    rationale: str | None
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AILeadAnalysisResponse(BaseModel):
    lead_id: int | None
    customer_id: int | None
    generated_at: datetime
    predictions: list[AIPredictionResponse]
