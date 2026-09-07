from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class LeadBase(BaseModel):
    source_channel: str | None = Field(
        default=None,
        max_length=64,
        alias="CRM_Channel",
        validation_alias=AliasChoices("CRM_Channel", "source_channel"),
    )
    source_medium: str | None = Field(
        default=None,
        max_length=64,
        alias="CRM_Data_Medium",
        validation_alias=AliasChoices("CRM_Data_Medium", "source_medium"),
    )
    status: str = Field(
        default="new",
        min_length=1,
        max_length=32,
        alias="Label_Source_Lead_Status",
        validation_alias=AliasChoices("Label_Source_Lead_Status", "status"),
    )
    current_stage: str = Field(default="generated", min_length=1, max_length=32)
    current_section: str | None = Field(default="intake", max_length=64)
    current_handler: str | None = Field(default=None, max_length=100)
    priority: str = Field(default="medium", min_length=1, max_length=16)
    lead_score: float | None = None
    recommended_action: str | None = Field(default=None, max_length=64)
    excel_fields: dict[str, Any] | None = Field(default=None, validation_alias=AliasChoices("excel_fields", "Excel_Fields"), serialization_alias="Excel_Fields")


class LeadCreate(LeadBase):
    customer_id: int = Field(
        ge=1,
        validation_alias=AliasChoices("customer_id", "Customer_ID"),
    )
    campaign_id: int | None = Field(default=None, ge=1)


class LeadUpdate(BaseModel):
    customer_id: int | None = Field(default=None, ge=1)
    campaign_id: int | None = Field(default=None, ge=1)
    source_channel: str | None = Field(default=None, max_length=64)
    source_medium: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    current_stage: str | None = Field(default=None, min_length=1, max_length=32)
    current_section: str | None = Field(default=None, max_length=64)
    current_handler: str | None = Field(default=None, max_length=100)
    priority: str | None = Field(default=None, min_length=1, max_length=16)
    lead_score: float | None = None
    recommended_action: str | None = Field(default=None, max_length=64)
    excel_fields: dict[str, Any] | None = Field(default=None, validation_alias=AliasChoices("excel_fields", "Excel_Fields"), serialization_alias="Excel_Fields")


class LeadRead(LeadBase):
    id: int
    customer_id: int
    campaign_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
