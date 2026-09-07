from datetime import date, datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CampaignBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
        validation_alias=AliasChoices("name", "CRM_UTM_Campaign"),
        serialization_alias="CRM_UTM_Campaign",
    )
    channel: str | None = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices("channel", "CRM_UTM_Source"),
        serialization_alias="CRM_UTM_Source",
    )
    status: str = Field(default="active", min_length=1, max_length=32)
    start_date: date | None = None
    end_date: date | None = None


class CampaignCreate(CampaignBase):
    code: str = Field(min_length=1, max_length=64)


class CampaignUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    channel: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    start_date: date | None = None
    end_date: date | None = None


class CampaignRead(CampaignBase):
    id: int
    code: str
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CampaignPerformance(BaseModel):
    campaign_id: int
    total_events: int
    by_channel: dict[str, int]
    by_metric: dict[str, int]
