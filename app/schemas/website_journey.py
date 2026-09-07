from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class WebsiteEventRead(BaseModel):
    id: int
    lead_id: int | None
    customer_id: int | None
    event_name: str
    step_name: str | None = Field(serialization_alias="WEB_Step_Name")
    step_number: int | None = Field(serialization_alias="WEB_Step_Number")
    device_type: str | None = Field(serialization_alias="WEB_Device_Type")
    is_repeat_visitor: bool = Field(serialization_alias="WEB_New_Vs_Repeat")
    event_payload: dict | None
    event_time: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class JourneySummary(BaseModel):
    lead_id: int
    total_events: int
    unique_event_names: list[str]
    last_event_time: datetime | None


class WebsiteJourneyQuery(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    device_type: str | None = Field(default=None, max_length=32)
