from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeadBase(BaseModel):
    source_channel: str | None = Field(default=None, max_length=64)
    source_medium: str | None = Field(default=None, max_length=64)
    status: str = Field(default="new", min_length=1, max_length=32)
    priority: str = Field(default="medium", min_length=1, max_length=16)


class LeadCreate(LeadBase):
    customer_id: int = Field(ge=1)
    campaign_id: int | None = Field(default=None, ge=1)


class LeadUpdate(BaseModel):
    customer_id: int | None = Field(default=None, ge=1)
    campaign_id: int | None = Field(default=None, ge=1)
    source_channel: str | None = Field(default=None, max_length=64)
    source_medium: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    priority: str | None = Field(default=None, min_length=1, max_length=16)


class LeadRead(LeadBase):
    id: int
    customer_id: int
    campaign_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
