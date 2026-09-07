from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportJobRequest(BaseModel):
    source_path: str = Field(min_length=1)
    dataset_name: str | None = Field(default=None, max_length=100)
    file_format: str | None = Field(default=None, max_length=10)


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
