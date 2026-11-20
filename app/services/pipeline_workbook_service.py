import base64
import binascii
import re
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from typing import Any
from zipfile import BadZipFile

from fastapi import HTTPException
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.core.excel_contract import (
    CALL_COLUMNS,
    CAMPAIGN_COLUMNS,
    CUSTOMER_COLUMNS,
    EVENT_COLUMNS,
    LEAD_COLUMNS,
    MESSAGE_COLUMNS,
    PRODUCT_COLUMNS,
    TARGET_COLUMNS,
    WEB_COLUMNS,
)
from app.models.campaign import Campaign
from app.models.call import Call
from app.models.customer import Customer
from app.models.data_import_job import DataImportJob
from app.models.engagement_event import EngagementEvent
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.lead_assignment import LeadAssignment
from app.models.lead_timeline_event import LeadTimelineEvent
from app.models.product import Product
from app.models.task import Task
from app.models.website_event import WebsiteEvent
from app.schemas.data_management import (
    DataLoadRowPreview,
    ImportJobRead,
    PipelineWorkbookApplyRequest,
    PipelineWorkbookApplyResponse,
    PipelineWorkbookEffect,
    PipelineWorkbookFieldQuality,
    PipelineWorkbookPreviewResponse,
    PipelineWorkbookQuality,
    PipelineWorkbookRequest,
)

REQUIRED_COLUMNS = set(
    (
        *LEAD_COLUMNS,
        *CUSTOMER_COLUMNS,
        *PRODUCT_COLUMNS,
        *CAMPAIGN_COLUMNS,
        *MESSAGE_COLUMNS,
        *CALL_COLUMNS,
        *WEB_COLUMNS,
        *EVENT_COLUMNS,
        *TARGET_COLUMNS,
    )
)
MAX_FILE_BYTES = 10_000_000
MAX_ROWS = 10_000
PREVIEW_LIMIT = 100


class PipelineWorkbookService:
    def preview(
        self,
        db: Session,
        payload: PipelineWorkbookRequest,
    ) -> PipelineWorkbookPreviewResponse:
        rows = self._read_workbook(payload)
        if not rows:
            raise HTTPException(status_code=400, detail="The dataset sheet has no data rows.")
        if len(rows) > MAX_ROWS:
            raise HTTPException(status_code=400, detail=f"Workbooks are limited to {MAX_ROWS} rows.")

        normalized, previews = self._normalize_rows(rows)
        valid = [row for row, preview in zip(normalized, previews) if preview.action != "invalid"]
        entities = self._resolve_entities(db, valid)
        for preview, row in zip(previews, normalized):
            if preview.action == "invalid":
                continue
            pair = (row["customer_external_id"], row["campaign_code"])
            if _pair_exists(pair, entities):
                preview.action = "skip" if payload.mode == "append" else "update"
            else:
                preview.action = "insert"
            preview.key = row["customer_external_id"]

        effects = self._effects(db, valid, entities, payload.mode)
        quality = self._quality_report(rows, previews)
        return PipelineWorkbookPreviewResponse(
            file_name=payload.file_name,
            row_count=len(rows),
            invalid_count=sum(preview.action == "invalid" for preview in previews),
            quality=quality,
            effects=effects,
            preview_rows=previews[:PREVIEW_LIMIT],
        )

    def apply(
        self,
        db: Session,
        payload: PipelineWorkbookApplyRequest,
    ) -> PipelineWorkbookApplyResponse:
        preview = self.preview(db, payload)
        if preview.invalid_count:
            raise HTTPException(
                status_code=400,
                detail=f"Workbook has {preview.invalid_count} invalid row(s). Fix them before applying.",
            )
        rows = self._normalize_rows(self._read_workbook(payload))[0]
        entities = self._resolve_entities(db, rows)
        products = entities["products"]
        campaigns = entities["campaigns"]
        customers = entities["customers"]
        leads = entities["leads"]
        now = datetime.now(UTC)

        new_count: dict[str, int] = {}
        update_count: dict[str, int] = {}
        skip_count: dict[str, int] = {}

        try:
            for row in rows:
                excel_fields = row["excel_fields"]
                product = products.get(row["product_code"])
                if product is None:
                    product = Product(
                        code=row["product_code"],
                        name=row["product_name"],
                        excel_fields=excel_fields,
                    )
                    db.add(product)
                    products[row["product_code"]] = product
                    new_count["products"] = new_count.get("products", 0) + 1

                campaign = campaigns.get(row["campaign_code"])
                if campaign is None:
                    campaign = Campaign(
                        code=row["campaign_code"],
                        name=row["campaign_name"],
                        channel=row["source_channel"],
                        status="active",
                        excel_fields=excel_fields,
                    )
                    db.add(campaign)
                    db.flush()
                    campaigns[row["campaign_code"]] = campaign
                    new_count["campaigns"] = new_count.get("campaigns", 0) + 1

                customer = customers.get(row["customer_external_id"])
                if customer is None:
                    customer = Customer(
                        external_customer_id=row["customer_external_id"],
                        **row["customer_fields"],
                        excel_fields=excel_fields,
                    )
                    db.add(customer)
                    db.flush()
                    customers[row["customer_external_id"]] = customer
                    new_count["customers"] = new_count.get("customers", 0) + 1
                elif payload.mode == "merge":
                    changed = False
                    for field, value in row["customer_fields"].items():
                        if getattr(customer, field) is None and value is not None:
                            setattr(customer, field, value)
                            changed = True
                    if customer.excel_fields is None:
                        customer.excel_fields = excel_fields
                        changed = True
                    if changed:
                        update_count["customers"] = update_count.get("customers", 0) + 1

                pair = (customer.id, campaign.id)
                lead = leads.get(pair)
                if lead is not None and payload.mode == "append":
                    skip_count["leads"] = skip_count.get("leads", 0) + 1
                    continue
                if lead is None:
                    lead = Lead(
                        customer_id=customer.id,
                        campaign_id=campaign.id,
                        source_channel=row["source_channel"],
                        source_medium=row["source_medium"],
                        status=row["status"],
                        current_stage=row["current_stage"],
                        current_section=row["current_section"],
                        current_handler=row["current_handler"],
                        priority=row["priority"],
                        lead_score=row["lead_score"],
                        recommended_action=row["recommended_action"],
                        excel_fields=excel_fields,
                    )
                    db.add(lead)
                    db.flush()
                    leads[pair] = lead
                    new_count["leads"] = new_count.get("leads", 0) + 1
                    self._add_assignment_and_timeline(db, lead, customer, row)
                    new_count["lead_assignments"] = new_count.get("lead_assignments", 0) + 1
                    new_count["lead_timeline_events"] = new_count.get("lead_timeline_events", 0) + 1
                elif payload.mode == "merge" and lead.excel_fields is None:
                    lead.excel_fields = excel_fields
                    update_count["leads"] = update_count.get("leads", 0) + 1

                self._add_missing_related_records(
                    db,
                    lead,
                    customer,
                    campaign,
                    row,
                    now,
                    new_count,
                )

            db.flush()
            effects = self._build_applied_effects(
                db,
                new_count,
                update_count,
                skip_count,
            )
            job = DataImportJob(
                dataset_name="pipeline_workbook",
                source_path=payload.file_name,
                status="completed",
                row_count=len(rows),
                valid_row_count=len(rows),
                invalid_row_count=0,
                details={
                    "mode": payload.mode,
                    "effects": [effect.model_dump() for effect in effects],
                    "file_format": "xlsx",
                },
                completed_at=now,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
        except Exception:
            db.rollback()
            raise

        return PipelineWorkbookApplyResponse(
            job=ImportJobRead.model_validate(job),
            mode=payload.mode,
            row_count=len(rows),
            effects=effects,
        )

    def _read_workbook(self, payload: PipelineWorkbookRequest) -> list[dict[str, Any]]:
        if not payload.file_name.lower().endswith(".xlsx"):
            raise HTTPException(status_code=400, detail="Choose an .xlsx workbook.")
        try:
            contents = base64.b64decode(payload.content_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Workbook upload is not valid base64 data.") from exc
        if len(contents) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Workbooks are limited to 10 MB.")

        try:
            workbook = load_workbook(BytesIO(contents), read_only=True, data_only=True)
        except (BadZipFile, InvalidFileException, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Could not read the Excel workbook.") from exc
        try:
            if "dataset" not in workbook.sheetnames:
                raise HTTPException(status_code=400, detail="Workbook must contain a 'dataset' sheet.")
            iterator = workbook["dataset"].iter_rows(values_only=True)
            header_row = next(iterator, None)
            if not header_row:
                raise HTTPException(status_code=400, detail="The dataset sheet has no header row.")
            headers = [str(value).strip() if value is not None else "" for value in header_row]
            if any(not header for header in headers) or len(headers) != len(set(headers)):
                raise HTTPException(status_code=400, detail="Workbook headers must be non-empty and unique.")
            missing = REQUIRED_COLUMNS - set(headers)
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Workbook is missing required source columns: {', '.join(sorted(missing))}",
                )
            rows = []
            for values in iterator:
                if not values or all(value is None for value in values):
                    continue
                rows.append(
                    {
                        headers[index]: self._json_value(value)
                        for index, value in enumerate(values)
                        if index < len(headers)
                    }
                )
                if len(rows) > MAX_ROWS:
                    break
            return rows
        finally:
            workbook.close()

    @staticmethod
    def _normalize_rows(
        rows: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[DataLoadRowPreview]]:
        normalized: list[dict[str, Any]] = []
        previews: list[DataLoadRowPreview] = []
        seen_pairs: set[tuple[str, str]] = set()
        for index, source in enumerate(rows, start=1):
            customer_id = _text(source.get("Customer_ID"), 64)
            product_code = _text(source.get("CRM_Product_Code"), 64) or f"PRD-{_slug(_text(source.get('CRM_Product_Name')) or customer_id, 50)}"
            product_name = _text(source.get("CRM_Product_Name"), 150) or _text(source.get("WEB_Plan_Type"), 150) or "Unknown Product"
            campaign_seed = (
                _text(source.get("CRM_UTM_Campaign"), 64)
                or _text(source.get("CRM_Data_Source_Platform"), 64)
                or _text(source.get("CRM_Channel"), 64)
            )
            campaign_code = campaign_seed or f"CMP-{_slug(product_code, 50)}"
            campaign_name = (
                _text(source.get("CRM_UTM_Campaign"), 150)
                or _text(source.get("CRM_Data_Source_Platform"), 150)
                or f"{product_name} Campaign"
            )
            issues = []
            if not customer_id:
                issues.append("Customer_ID is required.")
            if len(product_code) > 64 or len(campaign_code) > 64:
                issues.append("Product and campaign codes must not exceed 64 characters.")

            lead_pair = (customer_id, campaign_code)
            if customer_id and lead_pair in seen_pairs:
                issues.append("Duplicate customer and campaign combination in workbook.")
            seen_pairs.add(lead_pair)

            score = _lead_score(source)
            status_value = _status(source)
            row = {
                "source": source,
                "excel_fields": source,
                "customer_external_id": customer_id,
                "customer_fields": {
                    "crm_gender": _optional_text(source.get("CRM_Gender"), 32),
                    "crm_age_band": _optional_text(source.get("CRM_Age_Band"), 32),
                    "crm_income_band": _optional_text(source.get("CRM_Income_Band"), 32),
                    "crm_occupation": _optional_text(source.get("CRM_Occupation"), 100),
                    "crm_education": _optional_text(source.get("CRM_Education"), 100),
                    "crm_tobacco_user": _optional_text(source.get("CRM_Tobacco_User"), 16),
                    "crm_nonresident_flag": _optional_text(source.get("CRM_NonResident_Flag"), 16),
                    "crm_existing_plan_flag": _optional_text(source.get("CRM_Existing_Plan_Flag"), 64),
                },
                "product_code": product_code,
                "product_name": product_name,
                "campaign_code": campaign_code,
                "campaign_name": campaign_name,
                "source_channel": _source_channel(source),
                "source_medium": _source_medium(source),
                "status": status_value,
                "current_stage": _stage(status_value),
                "current_section": _text(source.get("CRM_Department"), 64) or "intake",
                "current_handler": _optional_text(source.get("CRM_Source"), 100),
                "lead_score": score,
                "priority": _priority(score),
                "recommended_action": _next_action(source),
            }
            normalized.append(row)
            previews.append(
                DataLoadRowPreview(
                    row=index,
                    action="invalid" if issues else "insert",
                    key=customer_id or None,
                    issues=issues,
                    details={
                        "customer_id": customer_id,
                        "product": product_name,
                        "campaign": campaign_name,
                        "lead_status": status_value,
                        "priority": row["priority"],
                    },
                )
            )
        return normalized, previews

    @staticmethod
    def _quality_report(
        rows: list[dict[str, Any]],
        previews: list[DataLoadRowPreview],
    ) -> PipelineWorkbookQuality:
        row_count = len(rows)
        fields = list(rows[0]) if rows else []
        field_completeness = []
        for field in fields:
            populated_count = sum(not _is_missing(row.get(field)) for row in rows)
            missing_count = row_count - populated_count
            field_completeness.append(
                PipelineWorkbookFieldQuality(
                    field=field,
                    populated_count=populated_count,
                    missing_count=missing_count,
                    completeness=populated_count / row_count if row_count else 0.0,
                )
            )
        return PipelineWorkbookQuality(
            inspected_rows=row_count,
            valid_rows=sum(preview.action != "invalid" for preview in previews),
            invalid_rows=sum(preview.action == "invalid" for preview in previews),
            fields_with_missing_values=sum(field.missing_count > 0 for field in field_completeness),
            field_completeness=field_completeness,
        )

    @staticmethod
    def _resolve_entities(db: Session, rows: list[dict[str, Any]]) -> dict[str, Any]:
        product_codes = {row["product_code"] for row in rows}
        campaign_codes = {row["campaign_code"] for row in rows}
        customer_ids = {row["customer_external_id"] for row in rows}
        products = _query_by_values(db, Product, Product.code, product_codes)
        campaigns = _query_by_values(db, Campaign, Campaign.code, campaign_codes)
        customers = _query_by_values(db, Customer, Customer.external_customer_id, customer_ids)
        lead_pairs = {
            (customers[row["customer_external_id"]].id, campaigns[row["campaign_code"]].id)
            for row in rows
            if row["customer_external_id"] in customers and row["campaign_code"] in campaigns
        }
        leads: dict[tuple[int, int], Lead] = {}
        existing_pairs: set[tuple[int, int]] = set()
        lead_pair_list = list(lead_pairs)
        for offset in range(0, len(lead_pair_list), 500):
            batch = lead_pair_list[offset : offset + 500]
            lead_stmt = select(Lead).where(tuple_(Lead.customer_id, Lead.campaign_id).in_(batch))
            for lead in db.scalars(lead_stmt).all():
                pair = (lead.customer_id, lead.campaign_id)
                existing_pairs.add(pair)
                leads[pair] = lead
        return {
            "product_codes": product_codes,
            "campaign_codes": campaign_codes,
            "customer_ids": customer_ids,
            "lead_pairs": existing_pairs,
            "products": products,
            "campaigns": campaigns,
            "customers": customers,
            "leads": leads,
        }

    @staticmethod
    def _effects(
        db: Session,
        rows: list[dict[str, Any]],
        entities: dict[str, Any],
        mode: str,
    ) -> list[PipelineWorkbookEffect]:
        unique_leads: dict[tuple[str, str], dict[str, Any]] = {
            (row["customer_external_id"], row["campaign_code"]): row for row in rows
        }
        new_lead_rows = [
            row for key, row in unique_leads.items() if not _pair_exists(key, entities)
        ]
        if mode == "append":
            related_rows = new_lead_rows
            related_leads: dict[tuple[int, int], Lead] = {}
        else:
            related_rows = rows
            related_leads = entities["leads"]
        lead_ids = {lead.id for lead in related_leads.values()}
        events = _existing_lead_ids(db, EngagementEvent, lead_ids)
        websites = _existing_lead_ids(db, WebsiteEvent, lead_ids)
        existing_tasks = {
            task.lead_id
            for task in db.scalars(select(Task).where(Task.lead_id.in_(lead_ids))).all()
        } if lead_ids else set()
        task_ids = {
            task.id
            for task in db.scalars(select(Task).where(Task.lead_id.in_(lead_ids))).all()
        } if lead_ids else set()
        existing_followups = {
            followup.task_id
            for followup in db.scalars(select(Followup).where(Followup.task_id.in_(task_ids))).all()
        } if task_ids else set()
        call_lead_ids = {
            call.lead_id
            for call in db.scalars(select(Call).where(Call.lead_id.in_(lead_ids))).all()
        } if lead_ids else set()
        new_calls = 0
        for row in related_rows:
            if _as_int(row["source"].get("CDR_Total_Calls")) <= 0:
                continue
            row_key = (row["customer_external_id"], row["campaign_code"])
            if not _pair_exists(row_key, entities):
                new_calls += 1
                continue
            lead = related_leads.get(
                (
                    entities["customers"][row["customer_external_id"]].id,
                    entities["campaigns"][row["campaign_code"]].id,
                )
            )
            if lead is not None and lead.id not in call_lead_ids:
                new_calls += 1
        customer_updates = len({
            row["customer_external_id"]
            for row in related_rows
            if row["customer_external_id"] in entities["customers"]
            and (
                entities["customers"][row["customer_external_id"]].excel_fields is None
                or any(
                    getattr(entities["customers"][row["customer_external_id"]], field) is None
                    and value is not None
                    for field, value in row["customer_fields"].items()
                )
            )
        })
        lead_updates = sum(
            lead.excel_fields is None
            for lead in related_leads.values()
        ) if mode == "merge" else 0

        effects = []
        expected = {
            "products": len(entities["product_codes"] - entities["products"].keys()),
            "campaigns": len(entities["campaign_codes"] - entities["campaigns"].keys()),
            "customers": len(entities["customer_ids"] - entities["customers"].keys()),
            "leads": len(new_lead_rows),
            "lead_assignments": len(new_lead_rows),
            "lead_timeline_events": len(new_lead_rows),
            "engagement_events": len(new_lead_rows) + sum(
                lead.id not in events for lead in related_leads.values()
            ),
            "website_events": len(new_lead_rows) + sum(
                lead.id not in websites for lead in related_leads.values()
            ),
            "tasks": len(new_lead_rows) + sum(
                lead.id not in existing_tasks for lead in related_leads.values()
            ),
            "followups": len(new_lead_rows) + sum(
                lead.id not in existing_followups for lead in related_leads.values()
            ),
            "calls": new_calls,
        }
        for name, model in (
            ("products", Product),
            ("campaigns", Campaign),
            ("customers", Customer),
            ("leads", Lead),
            ("lead_assignments", LeadAssignment),
            ("lead_timeline_events", LeadTimelineEvent),
            ("engagement_events", EngagementEvent),
            ("website_events", WebsiteEvent),
            ("tasks", Task),
            ("followups", Followup),
            ("calls", Call),
        ):
            current = int(db.scalar(select(func.count()).select_from(model)) or 0)
            updated = (
                customer_updates if name == "customers"
                else lead_updates if name == "leads"
                else 0
            )
            effects.append(
                PipelineWorkbookEffect(
                    dataset_name=name,
                    current_count=current,
                    insert_count=expected[name],
                    update_count=updated,
                    skip_count=(
                        len(rows) - len(new_lead_rows)
                        if name == "leads" and mode == "append"
                        else 0
                    ),
                )
            )
        return effects

    @staticmethod
    def _build_applied_effects(
        db: Session,
        inserted: dict[str, int],
        updated: dict[str, int],
        skipped: dict[str, int],
    ) -> list[PipelineWorkbookEffect]:
        effects = []
        for name, model in (
            ("products", Product),
            ("campaigns", Campaign),
            ("customers", Customer),
            ("leads", Lead),
            ("lead_assignments", LeadAssignment),
            ("lead_timeline_events", LeadTimelineEvent),
            ("engagement_events", EngagementEvent),
            ("website_events", WebsiteEvent),
            ("tasks", Task),
            ("followups", Followup),
            ("calls", Call),
        ):
            effects.append(
                PipelineWorkbookEffect(
                    dataset_name=name,
                    current_count=int(db.scalar(select(func.count()).select_from(model)) or 0),
                    insert_count=inserted.get(name, 0),
                    update_count=updated.get(name, 0),
                    skip_count=skipped.get(name, 0),
                )
            )
        return effects

    @staticmethod
    def _add_assignment_and_timeline(
        db: Session,
        lead: Lead,
        customer: Customer,
        row: dict[str, Any],
    ) -> None:
        source = row["source"]
        db.add(
            LeadAssignment(
                lead_id=lead.id,
                customer_id=customer.id,
                assignment_type="assign",
                to_section=lead.current_section,
                to_handler=lead.current_handler,
                reason="excel_preload",
                trigger="dataset",
                details={
                    "customer_id": customer.external_customer_id,
                    "crm_channel": _text(source.get("CRM_Channel"), 64),
                    "crm_lead_type": _text(source.get("CRM_Lead_Type"), 64),
                },
                excel_fields=row["excel_fields"],
                is_current=True,
            )
        )
        db.add(
            LeadTimelineEvent(
                lead_id=lead.id,
                customer_id=customer.id,
                event_type="lead_created",
                event_source="sample_data.xlsx",
                details={
                    "label_source_disposition": _text(source.get("Label_Source_Disposition"), 120),
                    "label_source_lead_status": _text(source.get("Label_Source_Lead_Status"), 120),
                    "label_basis": _text(source.get("Label_Basis"), 64),
                    "label_customer_validity": _as_int(source.get("LABEL_Customer_Validity")),
                },
                excel_fields=row["excel_fields"],
            )
        )

    @staticmethod
    def _add_missing_related_records(
        db: Session,
        lead: Lead,
        customer: Customer,
        campaign: Campaign,
        row: dict[str, Any],
        now: datetime,
        inserted: dict[str, int],
    ) -> None:
        source = row["source"]
        if db.scalar(select(EngagementEvent.id).where(EngagementEvent.lead_id == lead.id)) is None:
            db.add(
                EngagementEvent(
                    lead_id=lead.id,
                    customer_id=customer.id,
                    campaign_id=campaign.id,
                    channel=_engagement_channel(source),
                    metric_type="engaged",
                    metric_value=max(
                        1,
                        _as_int(source.get("Page_Views")),
                        _as_int(source.get("MSG_Engaged")),
                        _as_int(source.get("CDR_Connected_Calls")),
                    ),
                    event_payload={
                        key.lower(): _as_int(source.get(key))
                        for key in ("MSG_Sent", "MSG_Delivered", "MSG_Read", "MSG_Clicked")
                    },
                    excel_fields=row["excel_fields"],
                )
            )
            inserted["engagement_events"] = inserted.get("engagement_events", 0) + 1
        if db.scalar(select(WebsiteEvent.id).where(WebsiteEvent.lead_id == lead.id)) is None:
            step_name = _text(source.get("WEB_Step_Name"), 100) or "Unknown Step"
            db.add(
                WebsiteEvent(
                    lead_id=lead.id,
                    customer_id=customer.id,
                    event_name=_slug(step_name, 64),
                    step_name=step_name,
                    step_number=_as_int(source.get("WEB_Step_Number"), 1),
                    device_type=_text(source.get("WEB_Device_Type"), 32) or "unknown",
                    is_repeat_visitor=_as_bool(source.get("WEB_New_Vs_Repeat")),
                    event_payload={
                        "web_tracked": _as_int(source.get("WEB_Tracked")),
                        "visits": _as_int(source.get("Visits")),
                        "page_views": _as_int(source.get("Page_Views")),
                        "total_seconds_spent": _as_int(source.get("Total_Seconds_Spent")),
                        "plan_type": _text(source.get("WEB_Plan_Type"), 64),
                        "plan_variant": _text(source.get("WEB_Plan_Variant"), 64),
                        "quoted_price": _as_float(source.get("WEB_Quoted_Price")),
                        "coverage_amount": _as_float(source.get("WEB_Coverage_Amount")),
                    },
                    excel_fields=row["excel_fields"],
                )
            )
            inserted["website_events"] = inserted.get("website_events", 0) + 1
        task_title = f"Handle lead {customer.external_customer_id}"[:160]
        task = db.scalar(select(Task).where(Task.lead_id == lead.id, Task.title == task_title))
        if task is None:
            days = max(1, min(14, round(_as_float(source.get("CRM_Days_Create_To_Update"), 2.0))))
            task = Task(
                lead_id=lead.id,
                customer_id=customer.id,
                title=task_title,
                description=(
                    f"Disposition: {_text(source.get('Label_Source_Disposition'))}; "
                    f"LeadStatus: {_text(source.get('Label_Source_Lead_Status'))}; "
                    f"Basis: {_text(source.get('Label_Basis'))}"
                )[:1000],
                status="completed" if row["status"] == "converted" else "open",
                priority=row["priority"],
                due_at=now + timedelta(days=days),
                excel_fields=row["excel_fields"],
            )
            db.add(task)
            db.flush()
            inserted["tasks"] = inserted.get("tasks", 0) + 1
        if db.scalar(select(Followup.id).where(Followup.task_id == task.id)) is None:
            converted = row["status"] == "converted"
            db.add(
                Followup(
                    task_id=task.id,
                    lead_id=lead.id,
                    customer_id=customer.id,
                    channel="call" if _as_int(source.get("CDR_Total_Calls")) > 0 else "email",
                    notes=(
                        f"Next action: {row['recommended_action']}; "
                        f"Top call status: {_text(source.get('CDR_Top_Call_Status'))}"
                    )[:1000],
                    status="completed" if converted else "pending",
                    scheduled_at=now + timedelta(days=1),
                    completed_at=now if converted else None,
                    excel_fields=row["excel_fields"],
                )
            )
            inserted["followups"] = inserted.get("followups", 0) + 1
        if _as_int(source.get("CDR_Total_Calls")) > 0 and db.scalar(
            select(Call.id).where(Call.lead_id == lead.id, Call.customer_id == customer.id)
        ) is None:
            average_talk = max(30, _as_int(source.get("CDR_Avg_Talk_Sec"), 120))
            ended = now - timedelta(minutes=2)
            db.add(
                Call(
                    lead_id=lead.id,
                    customer_id=customer.id,
                    direction="inbound" if _as_int(source.get("CDR_Inbound_Calls")) > 0 else "outbound",
                    status="completed" if _as_int(source.get("CDR_Connected_Calls")) > 0 else "scheduled",
                    notes=f"Top status: {_text(source.get('CDR_Top_Call_Status'))}"[:1000],
                    started_at=ended - timedelta(seconds=average_talk),
                    ended_at=ended,
                    duration_seconds=average_talk,
                    excel_fields=row["excel_fields"],
                )
            )
            inserted["calls"] = inserted.get("calls", 0) + 1

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value


def _query_by_values(db: Session, model: type, column: Any, values: set[Any]) -> dict[Any, Any]:
    if not values:
        return {}
    result = {}
    values_list = list(values)
    for offset in range(0, len(values_list), 500):
        for item in db.scalars(
            select(model).where(column.in_(values_list[offset : offset + 500]))
        ).all():
            result[getattr(item, column.key)] = item
    return result


def _existing_lead_ids(db: Session, model: type, lead_ids: set[int]) -> set[int]:
    if not lead_ids:
        return set()
    return set(db.scalars(select(model.lead_id).where(model.lead_id.in_(lead_ids))).all())


def _pair_exists(key: tuple[str, str], entities: dict[str, Any]) -> bool:
    customer = entities["customers"].get(key[0])
    campaign = entities["campaigns"].get(key[1])
    return customer is not None and campaign is not None and (customer.id, campaign.id) in entities["lead_pairs"]


def _text(value: Any, max_len: int | None = None) -> str:
    text = "" if value is None else str(value).strip()
    return text[:max_len] if max_len is not None else text


def _is_missing(value: Any) -> bool:
    return value is None or isinstance(value, str) and not value.strip()


def _optional_text(value: Any, max_len: int | None = None) -> str | None:
    return _text(value, max_len) or None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value))) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value)) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    return _text(value).lower() in {"1", "true", "t", "yes", "y", "repeat"}


def _slug(value: str, max_len: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:max_len] or "x"


def _source_channel(row: dict[str, Any]) -> str:
    return (
        _text(row.get("CRM_Channel"), 64)
        or _text(row.get("CRM_Source"), 64)
        or _text(row.get("WEB_Last_Touch_Channel"), 64)
        or _text(row.get("CRM_Data_Source_Platform"), 64)
        or "unknown"
    )


def _source_medium(row: dict[str, Any]) -> str:
    return (
        _text(row.get("CRM_Data_Medium"), 64)
        or _text(row.get("CRM_Lead_Source"), 64)
        or _text(row.get("CRM_Lead_Type"), 64)
        or _text(row.get("WEB_Device_Type"), 64)
        or "unknown"
    )


def _engagement_channel(row: dict[str, Any]) -> str:
    raw = " ".join(
        _text(row.get(column))
        for column in ("CRM_Channel", "CRM_Data_Medium", "WEB_Last_Touch_Channel")
    ).lower()
    for token, channel in (("whatsapp", "whatsapp"), ("rcs", "rcs"), ("email", "email"), ("mail", "email")):
        if token in raw:
            return channel
    return "website"


def _status(row: dict[str, Any]) -> str:
    text = f"{_text(row.get('Label_Source_Lead_Status'))} {_text(row.get('Label_Source_Disposition'))}".lower()
    if any(token in text for token in ("converted", "payment", "closed", "sale")):
        return "converted"
    if any(token in text for token in ("interested", "follow", "contactable", "callback")):
        return "qualified"
    if any(token in text for token in ("lost", "invalid", "not interested", "reject")):
        return "lost"
    return "new"


def _lead_score(row: dict[str, Any]) -> float:
    event_count = sum(_as_int(value) for key, value in row.items() if key.startswith("ev_"))
    score = max(0.0, min(_as_float(row.get("CDR_Connect_Rate")), 1.0)) * 35.0
    score += min(_as_int(row.get("Page_Views")), 30) * 0.8
    score += min(_as_int(row.get("MSG_Engaged")), 20) * 0.6
    score += min(_as_int(row.get("WEB_Tracked")), 10) * 1.5
    score += min(_as_int(row.get("CRM_Contact_Count")), 10)
    score += min(event_count, 20) * 0.5
    return round(min(score, 100.0), 2)


def _priority(score: float) -> str:
    return "high" if score >= 70 else "medium" if score >= 40 else "low"


def _stage(status: str) -> str:
    return {
        "converted": "completed",
        "qualified": "nurturing",
        "lost": "closed",
    }.get(status, "generated")


def _next_action(row: dict[str, Any]) -> str:
    text = " ".join(
        _text(row.get(column))
        for column in ("Label_Source_Disposition", "CDR_Top_Q_Type", "Label_Source_Lead_Status")
    ).lower()
    if any(token in text for token in ("callback", "follow", "call")):
        return "call"
    if any(token in text for token in ("payment", "proposal", "otp", "convert")):
        return "close"
    return "engage"
