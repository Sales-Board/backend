from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EngagementEventRead(BaseModel):
    id: int
    lead_id: int | None
    customer_id: int | None
    campaign_id: int | None
    channel: str
    metric_type: str
    metric_value: int
    event_payload: dict | None
    event_time: datetime

    model_config = ConfigDict(from_attributes=True)
