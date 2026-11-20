from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ImportJobRequest(BaseModel):
    source_path: str = Field(min_length=1)
    dataset_name: str | None = Field(default=None, max_length=100)
    file_format: str | None = Field(default=None, max_length=10)


class DataLoadRequest(BaseModel):
    dataset_name: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    file_format: Literal["csv", "json"]
    content: str = Field(min_length=1, max_length=10_000_000)


class DataLoadDatasetInfo(BaseModel):
    name: str
    fields: list[str]
    required_fields: list[str]
    match_field: str


class DataLoadApplyRequest(DataLoadRequest):
    mode: Literal["merge", "append", "replace"]


class DataLoadRowPreview(BaseModel):
    row: int
    action: Literal["insert", "update", "skip", "invalid"]
    key: str | None = None
    issues: list[str] = Field(default_factory=list)


class DataLoadPreviewResponse(BaseModel):
    dataset_name: str
    file_name: str
    row_count: int
    current_count: int
    insert_count: int
    update_count: int
    skip_count: int
    invalid_count: int
    replace_delete_count: int
    replace_blocked_count: int
    replace_blocked_reason: str | None = None
    preview_rows: list[DataLoadRowPreview]


class ImportJobRead(BaseModel):
    id: int
    dataset_name: str
    source_path: str
    status: str
    row_count: int
    valid_row_count: int
    invalid_row_count: int
    error_message: str | None
    details: dict | None
    created_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DataLoadApplyResponse(BaseModel):
    job: ImportJobRead
    mode: Literal["merge", "append", "replace"]
    inserted_count: int
    updated_count: int
    skipped_count: int
    deleted_count: int


class DataQualityResponse(BaseModel):
    generated_at: datetime
    table_counts: dict[str, int]
    completeness: dict[str, float]


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str
    count: int


class ValidationResponse(BaseModel):
    generated_at: datetime
    total_issues: int
    issues: list[ValidationIssue]


class ExportRequest(BaseModel):
    resource: str = Field(min_length=1, max_length=50)
    file_format: str = Field(default="json", max_length=10)


class ExportResponse(BaseModel):
    job_id: int
    resource: str
    file_format: str
    file_path: str
    row_count: int
    status: str
