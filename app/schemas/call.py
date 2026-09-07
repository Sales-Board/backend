from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CallBase(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    direction: str = Field(default="outbound", min_length=1, max_length=16)
    status: str = Field(default="scheduled", min_length=1, max_length=32)
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
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
