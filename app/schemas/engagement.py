from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class EngagementEventRead(BaseModel):
    id: int
    lead_id: int | None
    customer_id: int | None
    campaign_id: int | None
    channel: str = Field(alias="CRM_Channel", validation_alias=AliasChoices("CRM_Channel", "channel"))
    metric_type: str
    metric_value: int = Field(alias="MSG_Engaged")
    event_payload: dict | None
    event_time: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
