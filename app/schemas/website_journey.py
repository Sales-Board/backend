from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WebsiteEventRead(BaseModel):
    id: int
    lead_id: int | None
    customer_id: int | None
    event_name: str
    step_name: str | None
    step_number: int | None
    device_type: str | None
    is_repeat_visitor: bool
    event_payload: dict | None
    event_time: datetime

    model_config = ConfigDict(from_attributes=True)


class JourneySummary(BaseModel):
    lead_id: int
    total_events: int
    unique_event_names: list[str]
    last_event_time: datetime | None


class WebsiteJourneyQuery(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    device_type: str | None = Field(default=None, max_length=32)
