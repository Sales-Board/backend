import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.data_repository import DataRepository
from app.schemas.data_management import (
    DataQualityResponse,
    ExportRequest,
    ExportResponse,
    ImportJobRead,
    ImportJobRequest,
    ValidationIssue,
    ValidationResponse,
)


class DataService:
    def __init__(self, repository: DataRepository | None = None) -> None:
        self.repository = repository or DataRepository()

    def import_data(self, db: Session, payload: ImportJobRequest) -> ImportJobRead:
        source = Path(payload.source_path).expanduser()
        dataset_name = payload.dataset_name or source.stem
        job = self.repository.create_import_job(db, dataset_name=dataset_name, source_path=str(source))

        if not source.exists() or not source.is_file():
            self.repository.fail_import_job(db, job, f"source file not found: {source}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source file not found")

        file_format = (payload.file_format or source.suffix.lstrip(".")).lower()
        required_fields = {
            "customers": ["external_customer_id"],
            "leads": ["customer_id"],
            "products": ["code", "name"],
            "campaigns": ["code", "name"],
            "calls": ["status"],
        }

        try:
            if file_format == "csv":
                rows = self._read_csv_rows(source)
            elif file_format == "json":
                rows = self._read_json_rows(source)
            else:
                raise ValueError(f"unsupported file format: {file_format}")

            fields = required_fields.get(dataset_name, [])
            valid_count, invalid_count = self._validate_rows(rows, fields)
            details = {
                "file_format": file_format,
                "required_fields": fields,
                "sample_columns": sorted(rows[0].keys()) if rows else [],
            }
            completed = self.repository.complete_import_job(
                db,
                job,
                row_count=len(rows),
                valid_row_count=valid_count,
                invalid_row_count=invalid_count,
                details=details,
            )
            return ImportJobRead.model_validate(completed)
        except Exception as exc:
            self.repository.fail_import_job(db, job, str(exc))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    def get_import_job(self, db: Session, job_id: int) -> ImportJobRead:
        job = self.repository.get_import_job(db, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
        return ImportJobRead.model_validate(job)

    def list_history(self, db: Session, skip: int = 0, limit: int = 100) -> list[ImportJobRead]:
        jobs = self.repository.list_import_jobs(db, skip=skip, limit=limit)
        return [ImportJobRead.model_validate(job) for job in jobs]

    def get_quality_report(self, db: Session) -> DataQualityResponse:
        counts = self.repository.table_counts(db)

        leads = counts["leads"]
        calls = counts["calls"]
        completeness = {
            "leads_with_customer_ratio": 0.0,
            "calls_completed_with_duration_ratio": 0.0,
        }

        if leads > 0:
            # customer_id is non-null in schema, so this ratio is 1.0 when leads exist.
            completeness["leads_with_customer_ratio"] = 1.0

        if calls > 0:
            missing = self.repository.completed_calls_missing_duration(db)
            completed = self.repository.completed_calls_count(db)
            if completed == 0:
                completeness["calls_completed_with_duration_ratio"] = 1.0
            else:
                completeness["calls_completed_with_duration_ratio"] = max(
                    0.0,
                    float(completed - missing) / float(completed),
                )

        return DataQualityResponse(generated_at=datetime.now(UTC), table_counts=counts, completeness=completeness)

    def get_validation_report(self, db: Session) -> ValidationResponse:
        issues: list[ValidationIssue] = []

        missing_duration = self.repository.completed_calls_missing_duration(db)
        if missing_duration > 0:
            issues.append(
                ValidationIssue(
                    code="CALL_DURATION_MISSING",
                    message="Completed calls without duration_seconds",
                    severity="warning",
                    count=missing_duration,
                )
            )

        end_before_start = self.repository.calls_with_end_before_start(db)
        if end_before_start > 0:
            issues.append(
                ValidationIssue(
                    code="CALL_END_BEFORE_START",
                    message="Calls where ended_at is earlier than started_at",
                    severity="error",
                    count=end_before_start,
                )
            )

        missing_external = self.repository.customers_missing_external_id(db)
        if missing_external > 0:
            issues.append(
                ValidationIssue(
                    code="CUSTOMER_EXTERNAL_ID_MISSING",
                    message="Customers missing external_customer_id",
                    severity="warning",
                    count=missing_external,
                )
            )

        return ValidationResponse(generated_at=datetime.now(UTC), total_issues=len(issues), issues=issues)

    def export_data(self, db: Session, payload: ExportRequest) -> ExportResponse:
        resource = payload.resource.strip().lower()
        file_format = payload.file_format.strip().lower()
        if file_format not in {"json", "csv"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_format must be json or csv")

        rows = self.repository.fetch_resource_rows(db, resource=resource)
        if resource not in {
            "customers",
            "leads",
            "products",
            "campaigns",
            "calls",
            "engagement_events",
            "website_events",
            "import_jobs",
        }:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported export resource")

        export_dir = Path(__file__).resolve().parents[1] / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output_path = export_dir / f"{resource}_{timestamp}.{file_format}"

        if file_format == "json":
            with output_path.open("w", encoding="utf-8") as handle:
                json.dump(rows, handle, ensure_ascii=True, indent=2)
        else:
            fieldnames = sorted(rows[0].keys()) if rows else []
            with output_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                if fieldnames:
                    writer.writeheader()
                    writer.writerows(rows)

        export_job = self.repository.create_import_job(
            db,
            dataset_name=f"export:{resource}",
            source_path=str(output_path),
        )
        export_job = self.repository.complete_import_job(
            db,
            export_job,
            row_count=len(rows),
            valid_row_count=len(rows),
            invalid_row_count=0,
            details={"export": True, "resource": resource, "file_format": file_format},
        )

        return ExportResponse(
            job_id=export_job.id,
            resource=resource,
            file_format=file_format,
            file_path=str(output_path),
            row_count=len(rows),
            status="completed",
        )

    @staticmethod
    def _read_csv_rows(source: Path) -> list[dict[str, str]]:
        with source.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]

    @staticmethod
    def _read_json_rows(source: Path) -> list[dict]:
        with source.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, list):
            return [item for item in loaded if isinstance(item, dict)]
        if isinstance(loaded, dict):
            return [loaded]
        raise ValueError("json payload must be an object or list of objects")

    @staticmethod
    def _validate_rows(rows: list[dict], required_fields: list[str]) -> tuple[int, int]:
        if not required_fields:
            return len(rows), 0

        valid_count = 0
        invalid_count = 0
        for row in rows:
            if all(str(row.get(field, "")).strip() != "" for field in required_fields):
                valid_count += 1
            else:
                invalid_count += 1
        return valid_count, invalid_count
