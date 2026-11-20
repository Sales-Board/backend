import csv
import json
from datetime import date, datetime
from io import StringIO
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.campaign import Campaign
from app.models.call import Call
from app.models.customer import Customer
from app.models.data_import_job import DataImportJob
from app.models.engagement_event import EngagementEvent
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.lead_assignment import LeadAssignment
from app.models.lead_outcome import LeadOutcome
from app.models.lead_timeline_event import LeadTimelineEvent
from app.models.product import Product
from app.models.task import Task
from app.models.website_event import WebsiteEvent
from app.schemas.data_management import (
    DataLoadApplyRequest,
    DataLoadApplyResponse,
    DataLoadDatasetInfo,
    DataLoadPreviewResponse,
    DataLoadRequest,
    DataLoadRowPreview,
    ImportJobRead,
)

DATASETS = {
    "customers": Customer,
    "leads": Lead,
    "products": Product,
    "campaigns": Campaign,
    "calls": Call,
    "tasks": Task,
    "followups": Followup,
    "engagement_events": EngagementEvent,
    "website_events": WebsiteEvent,
    "lead_assignments": LeadAssignment,
    "lead_outcomes": LeadOutcome,
    "lead_timeline_events": LeadTimelineEvent,
}
MATCH_FIELDS = {"customers": "external_customer_id", "products": "code", "campaigns": "code"}
MAX_ROWS = 10_000
PREVIEW_LIMIT = 100


class DataLoadService:
    @staticmethod
    def list_datasets() -> list[DataLoadDatasetInfo]:
        datasets = []
        for name, model in DATASETS.items():
            fields = [prop.key for prop in model.__mapper__.column_attrs]
            primary_key = next(iter(model.__mapper__.primary_key)).key
            match_field = MATCH_FIELDS.get(name, primary_key)
            required = [
                prop.key
                for prop in model.__mapper__.column_attrs
                if prop.key != primary_key
                and not prop.columns[0].nullable
                and prop.columns[0].server_default is None
                and prop.columns[0].default is None
            ]
            datasets.append(
                DataLoadDatasetInfo(
                    name=name,
                    fields=fields,
                    required_fields=required,
                    match_field=match_field,
                )
            )
        return datasets

    def preview(self, db: Session, payload: DataLoadRequest) -> DataLoadPreviewResponse:
        model = self._get_model(payload.dataset_name)
        rows = self._read_rows(payload)
        if not rows:
            raise HTTPException(status_code=400, detail="The file contains no data rows.")
        if len(rows) > MAX_ROWS:
            raise HTTPException(status_code=400, detail=f"Files are limited to {MAX_ROWS} rows.")

        normalized, row_previews = self._normalize_rows(db, model, payload.dataset_name, rows)
        key_attr = getattr(model, MATCH_FIELDS.get(payload.dataset_name, "id"))
        row_keys = [row.get(key_attr.key) for row in normalized if row.get(key_attr.key) is not None]
        existing = self._find_existing(db, model, key_attr, row_keys)
        existing_by_key = {getattr(item, key_attr.key): item for item in existing}

        inserted = updated = skipped = invalid = 0
        for preview in row_previews:
            if preview.action == "invalid":
                invalid += 1
                continue
            row_key = normalized[preview.row - 1].get(key_attr.key)
            if row_key is not None and row_key in existing_by_key:
                preview.action = "update"
                updated += 1
            else:
                preview.action = "insert"
                inserted += 1

        current_count = int(db.scalar(select(func.count()).select_from(model)) or 0)
        replace_delete_count = 0
        replace_blocked_count = 0
        replace_blocked_reason = None
        incoming_keys = set(row_keys)
        stale_query = select(model.id).where(~key_attr.in_(incoming_keys)) if incoming_keys else select(model.id)
        to_remove_ids = list(db.scalars(stale_query).all())
        replace_delete_count = len(to_remove_ids)
        replace_blocked_count = self._count_references(
            db,
            model,
            to_remove_ids,
        )
        primary_key = next(iter(model.__mapper__.primary_key)).key
        if key_attr.key == primary_key and any(row.get(primary_key) is None for row in normalized):
            replace_blocked_count = max(replace_blocked_count, 1)
            replace_blocked_reason = (
                f"Include the {primary_key} field in every row for a safe replacement."
            )

        return DataLoadPreviewResponse(
            dataset_name=payload.dataset_name,
            file_name=payload.file_name,
            row_count=len(rows),
            current_count=current_count,
            insert_count=inserted,
            update_count=updated,
            skip_count=skipped,
            invalid_count=invalid,
            replace_delete_count=replace_delete_count,
            replace_blocked_count=replace_blocked_count,
            replace_blocked_reason=replace_blocked_reason,
            preview_rows=row_previews[:PREVIEW_LIMIT],
        )

    def apply(self, db: Session, payload: DataLoadApplyRequest) -> DataLoadApplyResponse:
        preview = self.preview(db, payload)
        if preview.invalid_count:
            raise HTTPException(
                status_code=400,
                detail=f"Import has {preview.invalid_count} invalid row(s). Fix them before applying.",
            )
        if payload.mode == "replace" and preview.replace_blocked_reason:
            raise HTTPException(status_code=400, detail=preview.replace_blocked_reason)
        if payload.mode == "replace" and preview.replace_blocked_count:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot replace {payload.dataset_name}: "
                    f"{preview.replace_blocked_count} linked record(s) would be affected. "
                    "Remove or update dependent records first."
                ),
            )

        model = self._get_model(payload.dataset_name)
        rows = self._read_rows(payload)
        normalized, _ = self._normalize_rows(db, model, payload.dataset_name, rows)
        key_attr = getattr(model, MATCH_FIELDS.get(payload.dataset_name, "id"))
        row_keys = [row.get(key_attr.key) for row in normalized if row.get(key_attr.key) is not None]
        existing = self._find_existing(db, model, key_attr, row_keys)
        existing_by_key = {getattr(item, key_attr.key): item for item in existing}
        values_by_key = {row.get(key_attr.key): row for row in normalized}
        inserted = updated = skipped = deleted = 0

        try:
            for values in normalized:
                key = values.get(key_attr.key)
                current = existing_by_key.get(key) if key is not None else None
                if payload.mode == "append" and current is not None:
                    skipped += 1
                    continue
                if current is None:
                    db.add(model(**values))
                    inserted += 1
                    continue
                if payload.mode == "merge":
                    self._update_existing(current, values, db)
                    updated += 1

            if payload.mode == "replace":
                incoming_keys = set(row_keys)
                for key, current in existing_by_key.items():
                    self._update_existing(current, values_by_key[key], db)
                    updated += 1
                stale_query = (
                    select(model).where(~key_attr.in_(incoming_keys))
                    if incoming_keys
                    else select(model)
                )
                for current in db.scalars(stale_query).all():
                    db.delete(current)
                    deleted += 1

            db.flush()
            job = DataImportJob(
                dataset_name=payload.dataset_name,
                source_path=payload.file_name,
                status="completed",
                row_count=len(rows),
                valid_row_count=len(rows),
                invalid_row_count=0,
                details={
                    "mode": payload.mode,
                    "inserted_count": inserted,
                    "updated_count": updated,
                    "skipped_count": skipped,
                    "deleted_count": deleted,
                    "file_format": payload.file_format,
                },
                completed_at=datetime.now().astimezone(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Import could not be applied because a key or relationship conflicts with existing data.",
            ) from exc

        return DataLoadApplyResponse(
            job=ImportJobRead.model_validate(job),
            mode=payload.mode,
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
            deleted_count=deleted,
        )

    @staticmethod
    def _get_model(dataset_name: str) -> type:
        model = DATASETS.get(dataset_name)
        if model is None:
            supported = ", ".join(DATASETS)
            raise HTTPException(status_code=400, detail=f"Unsupported dataset. Choose one of: {supported}.")
        return model

    @staticmethod
    def _read_rows(payload: DataLoadRequest) -> list[dict[str, Any]]:
        try:
            if payload.file_format == "csv":
                reader = csv.DictReader(StringIO(payload.content))
                if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                    raise ValueError("CSV must have a header row with unique column names.")
                return [dict(row) for row in reader]
            parsed = json.loads(payload.content)
        except (csv.Error, json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Could not read the file: {exc}") from exc

        if isinstance(parsed, dict) and isinstance(parsed.get("rows"), list):
            parsed = parsed["rows"]
        if not isinstance(parsed, list) or any(not isinstance(row, dict) for row in parsed):
            raise HTTPException(status_code=400, detail="JSON data must be an array of row objects.")
        return parsed

    def _normalize_rows(
        self,
        db: Session,
        model: type,
        dataset_name: str,
        rows: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[DataLoadRowPreview]]:
        column_attrs = {prop.key: prop.columns[0] for prop in model.__mapper__.column_attrs}
        column_aliases = {
            alias: prop.key
            for prop in model.__mapper__.column_attrs
            for alias in (prop.key, prop.columns[0].name, prop.columns[0].key)
        }
        primary_key = next(iter(model.__mapper__.primary_key)).key
        key_name = MATCH_FIELDS.get(dataset_name, primary_key)
        normalized: list[dict[str, Any]] = []
        previews: list[DataLoadRowPreview] = []
        seen_keys: set[Any] = set()

        for row_number, raw in enumerate(rows, start=1):
            issues: list[str] = []
            if any(not isinstance(key, str) for key in raw):
                previews.append(DataLoadRowPreview(row=row_number, action="invalid", issues=["Column names must be strings."]))
                normalized.append({})
                continue

            values: dict[str, Any] = {}
            custom_fields: dict[str, Any] = {}
            for name, raw_value in raw.items():
                attr_name = column_aliases.get(name)
                if attr_name == "excel_fields":
                    if raw_value in (None, ""):
                        continue
                    try:
                        parsed_value = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
                        if not isinstance(parsed_value, dict):
                            raise ValueError("excel_fields must be a JSON object.")
                        custom_fields.update(parsed_value)
                    except (json.JSONDecodeError, ValueError) as exc:
                        issues.append(f"excel_fields: {exc}")
                    continue
                if attr_name is None:
                    if raw_value not in (None, ""):
                        custom_fields[name] = raw_value
                    continue
                column = column_attrs[attr_name]
                try:
                    value = self._coerce_value(raw_value, column.type.python_type)
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    issues.append(f"{name}: {exc}")
                    continue
                if value is not None:
                    values[attr_name] = value
                elif attr_name == primary_key:
                    continue
                elif column.nullable:
                    values[attr_name] = None

            for attr_name, column in column_attrs.items():
                if (
                    attr_name == primary_key
                    or column.nullable
                    or column.server_default is not None
                    or column.default is not None
                ):
                    continue
                if attr_name not in values:
                    issues.append(f"{attr_name}: required value is missing.")

            if custom_fields and "excel_fields" in column_attrs:
                values["excel_fields"] = custom_fields

            key = values.get(key_name)
            if key is not None and key in seen_keys:
                issues.append(f"{key_name}: duplicate key in uploaded file.")
            if key is not None:
                seen_keys.add(key)

            normalized.append(values)
            previews.append(
                DataLoadRowPreview(
                    row=row_number,
                    action="invalid" if issues else "insert",
                    key=str(key) if key is not None else None,
                    issues=issues,
                )
            )

        reference_values: dict[Any, set[Any]] = {}
        for values in normalized:
            for attr_name, value in values.items():
                if value is None:
                    continue
                for foreign_key in column_attrs[attr_name].foreign_keys:
                    reference_values.setdefault(foreign_key.column, set()).add(value)
        missing_references: dict[Any, set[Any]] = {}
        for target_column, values in reference_values.items():
            found = set(
                db.scalars(
                    select(target_column).where(target_column.in_(values))
                ).all()
            )
            missing_references[target_column] = values - found

        for row_number, values in enumerate(normalized):
            preview = previews[row_number]
            for attr_name, value in values.items():
                if value is None:
                    continue
                for foreign_key in column_attrs[attr_name].foreign_keys:
                    if value in missing_references.get(foreign_key.column, set()):
                        preview.issues.append(
                            f"{attr_name}: referenced {foreign_key.column.table.name} record not found."
                        )
            if preview.issues:
                preview.action = "invalid"
        return normalized, previews

    @staticmethod
    def _coerce_value(value: Any, python_type: type) -> Any:
        if value is None or value == "":
            return None
        if python_type is str:
            return str(value)
        if python_type is int:
            return int(value)
        if python_type is float:
            return float(value)
        if python_type is bool:
            if isinstance(value, bool):
                return value
            normalized = str(value).strip().lower()
            if normalized in {"true", "1", "yes"}:
                return True
            if normalized in {"false", "0", "no"}:
                return False
            raise ValueError("expected true/false.")
        if python_type is datetime:
            return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        if python_type is date:
            return value if isinstance(value, date) else date.fromisoformat(str(value))
        if python_type in {dict, list}:
            if isinstance(value, str):
                return json.loads(value)
            if isinstance(value, python_type):
                return value
            raise ValueError(f"expected {python_type.__name__}.")
        return value

    @staticmethod
    def _find_existing(db: Session, model: type, key_attr: Any, keys: list[Any]) -> list[Any]:
        if not keys:
            return []
        return list(db.scalars(select(model).where(key_attr.in_(set(keys)))).all())

    @staticmethod
    def _count_references(db: Session, model: type, ids: list[int]) -> int:
        if not ids:
            return 0
        target_table = model.__table__
        total = 0
        for table in Base.metadata.tables.values():
            for foreign_key in table.foreign_keys:
                if foreign_key.column.table is target_table:
                    total += int(
                        db.scalar(
                            select(func.count())
                            .select_from(table)
                            .where(table.c[foreign_key.parent.name].in_(ids))
                        )
                        or 0
                    )
        return total

    @staticmethod
    def _update_existing(current: Any, values: dict[str, Any], db: Session) -> None:
        primary_key = next(iter(current.__mapper__.primary_key)).key
        for name, value in values.items():
            if name == primary_key or value is None:
                continue
            if name == "excel_fields" and isinstance(value, dict):
                value = {**(current.excel_fields or {}), **value}
            setattr(current, name, value)
        db.add(current)
