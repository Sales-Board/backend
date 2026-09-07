from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CallBase(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    direction: str = Field(default="outbound", min_length=1, max_length=16, serialization_alias="CDR_Call_Direction")
    status: str = Field(
        default="scheduled",
        min_length=1,
        max_length=32,
        validation_alias=AliasChoices("status", "CDR_Top_Call_Status"),
        serialization_alias="CDR_Top_Call_Status",
    )
    phone_number: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    scheduled_at: datetime | None = None


class CallCreate(CallBase):
    pass


class CallUpdate(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    direction: str | None = Field(default=None, min_length=1, max_length=16)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    phone_number: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    scheduled_at: datetime | None = None


class CallStartRequest(BaseModel):
    started_at: datetime | None = None


class CallEndRequest(BaseModel):
    ended_at: datetime | None = None
    notes: str | None = None


class CallRead(CallBase):
    id: int
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None = Field(serialization_alias="CDR_Avg_Talk_Sec")
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
