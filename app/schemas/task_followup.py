from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    title: str = Field(
        min_length=1,
        max_length=160,
        validation_alias=AliasChoices("title", "Label_Source_Disposition"),
        serialization_alias="Label_Source_Disposition",
    )
    description: str | None = None
    status: str = Field(default="open", min_length=1, max_length=32)
    priority: str = Field(default="medium", min_length=1, max_length=16)
    due_at: datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    priority: str | None = Field(default=None, min_length=1, max_length=16)
    due_at: datetime | None = None


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FollowupBase(BaseModel):
    task_id: int | None = Field(default=None, ge=1)
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    channel: str = Field(default="call", min_length=1, max_length=32)
    notes: str | None = Field(default=None, serialization_alias="Label_Basis")
    status: str = Field(default="pending", min_length=1, max_length=32)
    scheduled_at: datetime | None = None


class FollowupCreate(FollowupBase):
    pass


class FollowupUpdate(BaseModel):
    task_id: int | None = Field(default=None, ge=1)
    lead_id: int | None = Field(default=None, ge=1)
    customer_id: int | None = Field(default=None, ge=1)
    channel: str | None = Field(default=None, min_length=1, max_length=32)
    notes: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None


class FollowupRead(FollowupBase):
    id: int
    completed_at: datetime | None
    created_at: datetime
    excel_fields: dict[str, Any] | None = Field(default=None, serialization_alias="Excel_Fields")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
