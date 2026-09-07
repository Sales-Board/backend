from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MLTrainRequest(BaseModel):
    model_name: str = Field(default="lead_conversion_baseline", min_length=1, max_length=100)


class MLTrainingJobRead(BaseModel):
    id: int
    model_name: str
    status: str
    training_rows: int
    metrics: dict | None
    artifact_path: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class MLModelSummary(BaseModel):
    model_name: str
    latest_job_id: int
    status: str
    training_rows: int
    created_at: datetime
