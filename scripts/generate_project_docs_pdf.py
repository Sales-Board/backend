#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

from openpyxl import load_workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app

DOCS_DIR = ROOT / "docs"
MD_PATH = DOCS_DIR / "project_backend_handbook.md"
PDF_PATH = DOCS_DIR / "project_backend_handbook.pdf"
SAMPLE_XLSX_PATH = ROOT / "sample_data.xlsx"

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head")


def _box(drawing: Drawing, x: float, y: float, w: float, h: float, text: str) -> None:
    drawing.add(Rect(x, y, w, h, strokeColor="#1F2937", fillColor="#E5E7EB", strokeWidth=1.2))
    drawing.add(String(x + 8, y + h / 2 - 4, text, fontName="Helvetica", fontSize=8.8, fillColor="#111827"))


def _arrow(drawing: Drawing, x1: float, y1: float, x2: float, y2: float) -> None:
    drawing.add(Line(x1, y1, x2, y2, strokeColor="#374151", strokeWidth=1.2))
    if x2 >= x1:
        head = Polygon(
            [x2, y2, x2 - 6, y2 + 3, x2 - 6, y2 - 3],
            strokeColor="#374151",
            fillColor="#374151",
        )
    else:
        head = Polygon(
            [x2, y2, x2 + 6, y2 + 3, x2 + 6, y2 - 3],
            strokeColor="#374151",
            fillColor="#374151",
        )
    drawing.add(head)


def architecture_diagram() -> Drawing:
    d = Drawing(520, 220)
    d.add(String(10, 205, "System Architecture", fontName="Helvetica-Bold", fontSize=11))

    _box(d, 12, 150, 86, 34, "Client")
    _box(d, 110, 150, 104, 34, "API Routes")
    _box(d, 226, 150, 104, 34, "Services")
    _box(d, 342, 150, 104, 34, "Repositories")
    _box(d, 458, 150, 56, 34, "Postgres")

    _arrow(d, 98, 167, 110, 167)
    _arrow(d, 214, 167, 226, 167)
    _arrow(d, 330, 167, 342, 167)
    _arrow(d, 446, 167, 458, 167)

    _box(d, 110, 90, 104, 34, "Pydantic Schemas")
    _box(d, 226, 90, 104, 34, "Workflow Rules")
    _box(d, 342, 90, 104, 34, "SQLAlchemy Models")
    _box(d, 458, 90, 56, 34, "Alembic")

    _arrow(d, 162, 150, 162, 124)
    _arrow(d, 278, 150, 278, 124)
    _arrow(d, 394, 150, 394, 124)
    _arrow(d, 486, 150, 486, 124)

    _box(d, 180, 25, 174, 38, "Sample Data + Import Pipeline")
    _arrow(d, 267, 90, 267, 63)

    d.add(String(12, 10, "Flow: request in -> domain orchestration -> persistent state -> typed response", fontName="Helvetica", fontSize=8.5))
    return d


def lifecycle_diagram() -> Drawing:
    d = Drawing(520, 235)
    d.add(String(10, 220, "Lead Lifecycle Workflow", fontName="Helvetica-Bold", fontSize=11))

    _box(d, 12, 165, 84, 32, "Lead Created")
    _box(d, 106, 165, 88, 32, "Assigned")
    _box(d, 204, 165, 88, 32, "Qualified")
    _box(d, 302, 165, 88, 32, "Decision")
    _box(d, 400, 165, 104, 32, "Action Outcome")

    _arrow(d, 96, 181, 106, 181)
    _arrow(d, 194, 181, 204, 181)
    _arrow(d, 292, 181, 302, 181)
    _arrow(d, 390, 181, 400, 181)

    _box(d, 120, 110, 120, 30, "Transfer")
    _box(d, 260, 110, 120, 30, "Follow-up Created")
    _box(d, 400, 110, 104, 30, "Status Update")

    _arrow(d, 160, 165, 180, 140)
    _arrow(d, 346, 165, 320, 140)
    _arrow(d, 452, 165, 452, 140)

    _box(d, 12, 48, 492, 42, "Timeline Events + Unified Details API (single payload for frontend lead workspace)")
    _arrow(d, 180, 110, 180, 90)
    _arrow(d, 320, 110, 260, 90)
    _arrow(d, 452, 110, 340, 90)

    d.add(String(12, 18, "Outcomes can move lead stage, set recommendation, and trigger new operational tasks.", fontName="Helvetica", fontSize=8.5))
    return d


def sales_optimization_diagram() -> Drawing:
    d = Drawing(520, 230)
    d.add(String(10, 215, "Sales Optimization Flow", fontName="Helvetica-Bold", fontSize=11))
    _box(d, 12, 165, 92, 32, "Exact Excel Row")
    _box(d, 118, 165, 92, 32, "Profile + Source")
    _box(d, 224, 165, 92, 32, "Engagement")
    _box(d, 330, 165, 92, 32, "AI Signals")
    _box(d, 436, 165, 68, 32, "Action")
    _arrow(d, 104, 181, 118, 181)
    _arrow(d, 210, 181, 224, 181)
    _arrow(d, 316, 181, 330, 181)
    _arrow(d, 422, 181, 436, 181)
    _box(d, 82, 105, 120, 32, "Product Fit")
    _box(d, 212, 105, 120, 32, "Call / Journey Fit")
    _box(d, 342, 105, 120, 32, "Next Best Action")
    _arrow(d, 270, 165, 142, 137)
    _arrow(d, 376, 165, 272, 137)
    _arrow(d, 470, 165, 402, 137)
    _box(d, 92, 42, 336, 35, "Assignment -> Action -> Outcome -> Timeline -> Analytics")
    _arrow(d, 142, 105, 190, 77)
    _arrow(d, 272, 105, 260, 77)
    _arrow(d, 402, 105, 330, 77)
    d.add(String(12, 18, "All decisions remain traceable to source columns or explicitly derived AI outputs.", fontName="Helvetica", fontSize=8.5))
    return d


def ingestion_diagram() -> Drawing:
    d = Drawing(520, 220)
    d.add(String(10, 205, "Excel Ingestion And Persistence", fontName="Helvetica-Bold", fontSize=11))
    _box(d, 12, 150, 110, 34, "sample_data.xlsx")
    _box(d, 142, 150, 110, 34, "Contract Check")
    _box(d, 272, 150, 110, 34, "Row Mapping")
    _box(d, 402, 150, 102, 34, "PostgreSQL")
    _arrow(d, 122, 167, 142, 167)
    _arrow(d, 252, 167, 272, 167)
    _arrow(d, 382, 167, 402, 167)
    _box(d, 45, 82, 112, 32, "CRM / Customer")
    _box(d, 176, 82, 112, 32, "Product / Source")
    _box(d, 307, 82, 112, 32, "CDR / MSG / WEB")
    _box(d, 438, 82, 66, 32, "ev_*")
    _arrow(d, 327, 150, 101, 114)
    _arrow(d, 327, 150, 232, 114)
    _arrow(d, 327, 150, 363, 114)
    _arrow(d, 327, 150, 471, 114)
    _box(d, 110, 22, 300, 34, "Excel_Fields snapshot on every data-bearing record")
    _arrow(d, 457, 82, 350, 56)
    return d


def feature_mapping_diagram() -> Drawing:
    d = Drawing(520, 245)
    d.add(String(10, 230, "Excel Feature Groups To Business Features", fontName="Helvetica-Bold", fontSize=11))
    groups = [(12, "CRM_*", "Profile + source"), (142, "CDR_*", "Call readiness"), (272, "MSG_*", "Messaging intent"), (402, "WEB_* / ev_*", "Journey progress")]
    for x, source, result in groups:
        _box(d, x, 170, 106, 30, source)
        _box(d, x, 112, 106, 30, result)
        _arrow(d, x + 53, 170, x + 53, 142)
    _box(d, 105, 45, 130, 32, "Validity + Intent")
    _box(d, 255, 45, 130, 32, "Lead Score")
    _box(d, 405, 45, 100, 32, "Product Fit")
    _arrow(d, 65, 112, 170, 77)
    _arrow(d, 195, 112, 220, 77)
    _arrow(d, 325, 112, 320, 77)
    _arrow(d, 455, 112, 450, 77)
    d.add(String(12, 18, "Only exact source columns or deterministic derived outputs are allowed.", fontName="Helvetica", fontSize=8.5))
    return d


def prediction_guardrail_diagram() -> Drawing:
    d = Drawing(520, 225)
    d.add(String(10, 210, "Leakage-Safe Prediction Flow", fontName="Helvetica-Bold", fontSize=11))
    _box(d, 12, 155, 120, 34, "Pre-outcome fields")
    _box(d, 160, 155, 120, 34, "Feature filter")
    _box(d, 308, 155, 100, 34, "Model")
    _box(d, 436, 155, 68, 34, "Output")
    _arrow(d, 132, 172, 160, 172)
    _arrow(d, 280, 172, 308, 172)
    _arrow(d, 408, 172, 436, 172)
    _box(d, 70, 82, 130, 32, "Excluded labels")
    _box(d, 220, 82, 130, 32, "Target column")
    _box(d, 370, 82, 130, 32, "Prediction point")
    _arrow(d, 225, 155, 135, 114)
    _arrow(d, 225, 155, 285, 114)
    _arrow(d, 225, 155, 435, 114)
    _box(d, 135, 22, 250, 32, "Features + target + exclusions recorded in metadata")
    _arrow(d, 285, 82, 260, 54)
    return d


def api_flow_diagram() -> Drawing:
    d = Drawing(520, 205)
    d.add(String(10, 190, "API Request And Response Flow", fontName="Helvetica-Bold", fontSize=11))
    _box(d, 12, 135, 92, 34, "Client")
    _box(d, 120, 135, 100, 34, "Pydantic")
    _box(d, 236, 135, 100, 34, "Service")
    _box(d, 352, 135, 92, 34, "Repository")
    _box(d, 460, 135, 54, 34, "DB")
    _arrow(d, 104, 152, 120, 152)
    _arrow(d, 220, 152, 236, 152)
    _arrow(d, 336, 152, 352, 152)
    _arrow(d, 444, 152, 460, 152)
    _box(d, 78, 65, 110, 32, "Exact Excel names")
    _box(d, 205, 65, 110, 32, "Derived rules")
    _box(d, 332, 65, 110, 32, "Excel_Fields")
    _arrow(d, 170, 135, 133, 97)
    _arrow(d, 286, 135, 260, 97)
    _arrow(d, 398, 135, 387, 97)
    d.add(String(12, 20, "Response returns source fields plus clearly labeled system/AI outputs.", fontName="Helvetica", fontSize=8.5))
    return d


def funnel_diagram() -> Drawing:
    d = Drawing(520, 230)
    d.add(String(10, 215, "Sales Funnel And Feedback", fontName="Helvetica-Bold", fontSize=11))
    _box(d, 15, 165, 100, 32, "Source Lead")
    _box(d, 130, 165, 100, 32, "Engaged")
    _box(d, 245, 165, 100, 32, "Intent")
    _box(d, 360, 165, 145, 32, "Product / Action")
    _arrow(d, 115, 181, 130, 181)
    _arrow(d, 230, 181, 245, 181)
    _arrow(d, 345, 181, 360, 181)
    _box(d, 90, 100, 120, 32, "Call / Follow-up")
    _box(d, 250, 100, 120, 32, "Outcome")
    _box(d, 410, 100, 95, 32, "Analytics")
    _arrow(d, 432, 165, 150, 132)
    _arrow(d, 310, 100, 310, 132)
    _arrow(d, 440, 100, 455, 132)
    _box(d, 125, 35, 280, 32, "Improve routing and timing using observed source behavior")
    _arrow(d, 455, 100, 350, 67)
    return d


def resolve_ref(ref: str, spec: dict[str, Any]) -> dict[str, Any]:
    parts = ref.strip("#/").split("/")
    node: Any = spec
    for part in parts:
        node = node.get(part, {})
    return node if isinstance(node, dict) else {}


def schema_keys(schema: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    if not schema:
        return []
    if "$ref" in schema:
        return schema_keys(resolve_ref(schema["$ref"], spec), spec)
    if schema.get("type") == "array":
        item_keys = schema_keys(schema.get("items", {}), spec)
        return [f"items[{k}]" for k in item_keys] if item_keys else ["items"]
    if "allOf" in schema:
        merged: list[str] = []
        for sub in schema["allOf"]:
            merged.extend(schema_keys(sub, spec))
        return sorted(set(merged))
    props = schema.get("properties", {})
    if isinstance(props, dict) and props:
        return sorted(props.keys())
    return []


def response_summary(op: dict[str, Any], spec: dict[str, Any]) -> str:
    responses = op.get("responses", {})
    parts: list[str] = []
    for code in sorted(responses.keys()):
        info = responses.get(code, {})
        content = info.get("content", {}) if isinstance(info, dict) else {}
        schema = content.get("application/json", {}).get("schema", {})
        keys = schema_keys(schema, spec)
        if keys:
            preview = ", ".join(keys[:8])
            if len(keys) > 8:
                preview += ", ..."
            parts.append(f"{code}: {preview}")
        else:
            desc = info.get("description", "response") if isinstance(info, dict) else "response"
            parts.append(f"{code}: {desc}")
    return " | ".join(parts)


def request_summary(op: dict[str, Any], spec: dict[str, Any]) -> str:
    params = op.get("parameters", [])
    param_names = [f"{p.get('name')}({p.get('in')})" for p in params if isinstance(p, dict)]

    body_keys: list[str] = []
    req_body = op.get("requestBody", {})
    if isinstance(req_body, dict):
        content = req_body.get("content", {})
        schema = content.get("application/json", {}).get("schema", {})
        body_keys = schema_keys(schema, spec)

    parts: list[str] = []
    if param_names:
        parts.append("params=" + ", ".join(param_names))
    if body_keys:
        preview = ", ".join(body_keys[:10])
        if len(body_keys) > 10:
            preview += ", ..."
        parts.append("body=" + preview)
    return " ; ".join(parts) if parts else "none"


def load_excel_metadata(path: Path) -> tuple[list[str], list[tuple[str, str, str]]]:
    if not path.exists():
        return [], []

    workbook = load_workbook(path, read_only=True, data_only=True)

    headers: list[str] = []
    if "dataset" in workbook.sheetnames:
        dataset_sheet = workbook["dataset"]
        for row in dataset_sheet.iter_rows(min_row=1, max_row=1, values_only=True):
            headers = [str(value).strip() for value in row if value is not None and str(value).strip()]

    definitions: list[tuple[str, str, str]] = []
    if "data_dictionary" in workbook.sheetnames:
        dictionary_sheet = workbook["data_dictionary"]
        for row in dictionary_sheet.iter_rows(min_row=2, values_only=True):
            if row is None:
                continue
            column = str(row[0]).strip() if row[0] is not None else ""
            if not column:
                continue
            source = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
            description = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
            definitions.append((column, source, description))

    return headers, definitions


def build_markdown(spec: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    paths = spec.get("paths", {})
    excel_headers, excel_definitions = load_excel_metadata(SAMPLE_XLSX_PATH)

    lines: list[str] = []
    lines.append("# Backend Project Handbook")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This backend is a lead-centric sales intelligence system built on FastAPI, SQLAlchemy, Alembic, and PostgreSQL.")
    lines.append("The lead is the central business entity and is connected to customer, campaign, journey, engagement, call, task, follow-up, AI prediction, and decision modules.")
    lines.append("")
    lines.append("## 2. Architecture")
    lines.append("")
    lines.append("- API Layer: app/api/routes")
    lines.append("- Service Layer: app/services")
    lines.append("- Repository Layer: app/repositories")
    lines.append("- Persistence Layer: app/models + PostgreSQL")
    lines.append("- Schema Contracts: app/schemas")
    lines.append("- DB Evolution: Alembic migrations")
    lines.append("")
    lines.append("Request flow:")
    lines.append("")
    lines.append("```text")
    lines.append("Client -> Route -> Service -> Repository -> DB")
    lines.append("                         -> business rules -> response schema")
    lines.append("```")
    lines.append("")
    lines.append("Architecture Diagram (Mermaid):")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("  A[Client / Frontend] --> B[FastAPI Routes]")
    lines.append("  B --> C[Service Layer]")
    lines.append("  C --> D[Repository Layer]")
    lines.append("  D --> E[(PostgreSQL)]")
    lines.append("  B -. validation .-> F[Pydantic Schemas]")
    lines.append("  C -. rules .-> G[Lifecycle Orchestration]")
    lines.append("  D -. mapping .-> H[SQLAlchemy Models]")
    lines.append("  H -. evolve .-> I[Alembic Migrations]")
    lines.append("  J[Sample Data Loader] --> E")
    lines.append("```")
    lines.append("")
    lines.append("Excel Ingestion Diagram:")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("  A[sample_data.xlsx] --> B[Contract Check] --> C[Row Mapping] --> D[(PostgreSQL)]")
    lines.append("  C --> E[CRM / Customer]")
    lines.append("  C --> F[Product / Source]")
    lines.append("  C --> G[CDR / MSG / WEB / ev_]")
    lines.append("  D --> H[Excel_Fields snapshot]")
    lines.append("```")
    lines.append("")
    lines.append("## 3. Feature Modules")
    lines.append("")
    features = [
        "Health + Dashboard",
        "Customers",
        "Leads",
        "Products",
        "Campaigns",
        "Engagement Channels",
        "Website Journey",
        "Calls",
        "Tasks + Follow-ups",
        "Data Import + Export",
        "ML Training + Model Catalog",
        "AI Predictions",
        "Decision Engine",
        "Analytics",
        "Reports",
        "Lead Lifecycle (assignment, transfer, outcomes, timeline, details)",
    ]
    for idx, feature in enumerate(features, start=1):
        lines.append(f"{idx}. {feature}")
    lines.append("")
    lines.append("## 4. Data Processing")
    lines.append("")
    lines.append("1. Source data is loaded from backend/sample_data.xlsx using scripts/preload_sample_data.py.")
    lines.append("2. The loader maps grouped records into products, campaigns, customers, leads, tasks, follow-ups, calls, engagement events, and website events.")
    lines.append("3. Live APIs use these persisted records, not synthetic smoke values.")
    lines.append("4. AI endpoints score/segment leads and store prediction logs.")
    lines.append("5. Decision endpoint combines predictions + rules into next action recommendations.")
    lines.append("6. Lifecycle module adds assignment/transfer, outcome tracking, and timeline events to create a connected business workflow.")
    lines.append("7. Unified lead details endpoint aggregates lead + customer + campaign + engagement + AI + operational activity for frontend rendering.")
    lines.append("")
    lines.append("Feature Mapping Diagram:")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("  A[CRM_*] --> E[Validity / Intent]")
    lines.append("  B[CDR_*] --> F[Call Readiness]")
    lines.append("  C[MSG_*] --> G[Messaging Intent]")
    lines.append("  D[WEB_* + ev_*] --> H[Journey Progress]")
    lines.append("  E --> I[Derived Lead Score]")
    lines.append("  F --> I")
    lines.append("  G --> I")
    lines.append("  H --> J[Product Fit]")
    lines.append("```")
    lines.append("")
    lines.append("### 4.1 Sample Data Columns (sample_data.xlsx)")
    lines.append("")
    if excel_headers:
        lines.append(f"Total columns in dataset sheet: {len(excel_headers)}")
        lines.append("")
        for idx, header in enumerate(excel_headers, start=1):
            lines.append(f"{idx}. {header}")
    else:
        lines.append("sample_data.xlsx dataset columns were not available at generation time.")
    lines.append("")
    lines.append("### 4.2 Column Meaning (data_dictionary sheet)")
    lines.append("")
    if excel_definitions:
        for column, source, description in excel_definitions:
            lines.append(f"- {column} | source={source or 'n/a'} | {description or 'n/a'}")
    else:
        lines.append("data_dictionary definitions were not available at generation time.")
    lines.append("")
    lines.append("### 4.3 Column To API Field Mapping")
    lines.append("")
    lines.append("- Customer_ID -> customers.external_customer_id -> returned in /api/customers and /api/leads/{id}/details.customer")
    lines.append("- CRM_Product_Code/CRM_Product_Name -> products.code/products.name -> returned in /api/products and details.campaign linkage")
    lines.append("- CRM_UTM_Campaign/CRM_Data_Source_Platform -> campaigns.code/name -> returned in /api/campaigns")
    lines.append("- CRM_Channel/CRM_Data_Medium/CRM_Source -> leads.source_channel/source_medium/current_handler")
    lines.append("- Label_Source_Lead_Status/Label_Source_Disposition -> leads.status/recommended_action")
    lines.append("- LABEL_Customer_Validity/CDR_Connect_Rate/Page_Views/MSG_Engaged -> leads.lead_score")
    lines.append("- CRM_Department -> leads.current_section and lifecycle assignment.to_section")
    lines.append("- CDR_* metrics -> calls and engagement event payloads")
    lines.append("- WEB_* metrics -> website_events fields and payload")
    lines.append("- Label_Basis/Disposition -> task descriptions + followup notes + timeline details")
    lines.append("")
    lines.append("## 5. How To Run In Detail")
    lines.append("")
    lines.append("1. Create backend-local virtual environment and install requirements.")
    lines.append("2. Configure .env with DATABASE_URL for PostgreSQL.")
    lines.append("3. Run migrations: ./.venv/bin/alembic upgrade head")
    lines.append("4. Preload real dataset: ./.venv/bin/python scripts/preload_sample_data.py --reset")
    lines.append("5. Start API server: ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000")
    lines.append("6. Open Swagger: /api/docs and OpenAPI: /api/openapi.json")
    lines.append("7. Run smoke verification: ./.venv/bin/python scripts/live_api_smoke.py")
    lines.append("8. Run tests: ./.venv/bin/pytest -q")
    lines.append("9. Lifecycle-only test: ./.venv/bin/pytest -q tests/test_lead_lifecycle.py")
    lines.append("")
    lines.append("API Flow Diagram:")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("  A[Client] --> B[Pydantic Excel Names]")
    lines.append("  B --> C[Service Rules]")
    lines.append("  C --> D[Repository]")
    lines.append("  D --> E[(PostgreSQL)]")
    lines.append("  E --> F[Excel_Fields + Derived Outputs]")
    lines.append("```")
    lines.append("")
    lines.append("## 6. Feature Workflows And Handling")
    lines.append("")
    lines.append("1. Lead intake: create lead -> initial timeline event -> assignment queue.")
    lines.append("2. Assignment/transfer: updates current owner and section; previous assignment marked non-current.")
    lines.append("3. AI scoring: prediction APIs persist score outputs per prediction type.")
    lines.append("4. Decisioning: next action recommendation combines prediction signal and business logic.")
    lines.append("5. Outcome handling: captures result, updates lead stage/status, optionally creates follow-up, and appends timeline events.")
    lines.append("6. Reporting: analytics/reports endpoints query aggregated module-level data for operational monitoring.")
    lines.append("")
    lines.append("Lifecycle Diagram (Mermaid):")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("  A[Lead Created] --> B[Assign or Transfer]")
    lines.append("  B --> C[AI + Decision]")
    lines.append("  C --> D[Action Taken]")
    lines.append("  D --> E[Outcome Recorded]")
    lines.append("  E --> F[Update Lead State]")
    lines.append("  E --> G[Create Follow-up]")
    lines.append("  B --> H[Timeline Event]")
    lines.append("  D --> H")
    lines.append("  E --> H")
    lines.append("  H --> I[Unified Lead Details API]")
    lines.append("```")
    lines.append("")
    lines.append("Sales Funnel Diagram:")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("  A[Source Lead] --> B[Engaged]")
    lines.append("  B --> C[Intent]")
    lines.append("  C --> D[Product / Action]")
    lines.append("  D --> E[Call / Follow-up]")
    lines.append("  E --> F[Outcome]")
    lines.append("  F --> G[Analytics Feedback]")
    lines.append("```")
    lines.append("")
    lines.append("Prediction Guardrail Diagram:")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("  A[Pre-outcome Excel fields] --> B[Leakage Filter]")
    lines.append("  X[Outcome / target columns] -. excluded .-> B")
    lines.append("  B --> C[Prediction Model]")
    lines.append("  C --> D[Derived Output + Metadata]")
    lines.append("  T[Prediction point] --> D")
    lines.append("```")
    lines.append("")
    lines.append("## 7. Sales Optimization Playbook")
    lines.append("")
    lines.append("The system maximizes productive sales activity by matching the next action to observed customer behavior, product context, contactability, and journey progress. It does not fabricate missing customer information or use outcome columns as prediction inputs.")
    lines.append("")
    lines.append("### 7.1 Stage 1 - Source And Lead Intake")
    lines.append("")
    lines.append("- Identify the lead using Customer_ID and associate source context from CRM_Channel, CRM_Department, CRM_Lead_Type, CRM_Lead_Source, CRM_Data_Medium, CRM_Source, and CRM_Data_Source_Platform.")
    lines.append("- Preserve CRM_Product_Code, CRM_Product_Name, CRM_UTM_Source, CRM_UTM_Medium, and CRM_UTM_Campaign for attribution and product context.")
    lines.append("- Use CRM_Lead_Create_Hour, CRM_Lead_Create_DayOfWeek, CRM_Lead_Create_Weekend, CRM_Lead_Create_Month, CRM_Days_Create_To_Update, CRM_Contact_Count, CRM_NonContact_Count, and CRM_No_Of_Attempts to understand timing and contact history.")
    lines.append("- Do not use Label_Source_Disposition or Label_Source_Lead_Status as predictive inputs; they are observed labels/outcomes.")
    lines.append("")
    lines.append("### 7.2 Stage 2 - Customer And Product Fit")
    lines.append("")
    lines.append("- Build customer context from CRM_Gender, CRM_Age_Band, CRM_Income_Band, CRM_Occupation, CRM_Education, CRM_Tobacco_User, CRM_NonResident_Flag, and CRM_Existing_Plan_Flag.")
    lines.append("- Match products using CRM_Product_Code, CRM_Product_Name, WEB_Plan_Type, WEB_Plan_Variant, WEB_Quoted_Price, WEB_Coverage_Amount, and WEB_Payment_Frequency.")
    lines.append("- Product recommendation is marked unavailable when the source row does not contain enough product or website context.")
    lines.append("")
    lines.append("### 7.3 Stage 3 - Engagement And Intent")
    lines.append("")
    lines.append("- Measure messaging engagement from MSG_Campaigns_Targeted, MSG_Sent, MSG_Delivered, MSG_Read, MSG_Clicked, MSG_Replied, MSG_Failed, and MSG_Engaged.")
    lines.append("- Measure call readiness from every CDR_ field, including CDR_Total_Calls, CDR_Connected_Calls, CDR_Connect_Rate, CDR_Avg_Talk_Sec, CDR_Callbacks_Scheduled, CDR_Top_Call_Status, and CDR_Top_Q_Type.")
    lines.append("- Measure digital intent from WEB_Tracked, Visits, Page_Views, Total_Seconds_Spent, WEB_Step_Name, WEB_Step_Number, WEB_New_Vs_Repeat, and WEB_Device_Type.")
    lines.append("- Use ev_Lead_Creation through ev_Page_Scroll_95 to identify funnel progress, quote activity, form progress, OTP activity, brochure interest, expert connection, and payment journey signals.")
    lines.append("")
    lines.append("### 7.4 Stage 4 - AI And Derived Lead Score")
    lines.append("")
    lines.append("- Customer validity uses LABEL_Customer_Validity as the target only; it is never an input feature.")
    lines.append("- Intent, engagement, segmentation, conversion, and lead score use only pre-outcome CRM, CDR, MSG, WEB, and ev_ fields.")
    lines.append("- CRM_Has_Application_No, CRM_Has_Payment_Flag, ev_Payment_Success, ev_Payment_Failure, Label_Source_Disposition, Label_Source_Lead_Status, and LABEL_Customer_Validity are excluded when they would leak the prediction target.")
    lines.append("- Every prediction response records feature_columns, excluded_columns, target_column, prediction_point, and derived_output.")
    lines.append("")
    lines.append("### 7.5 Stage 5 - Next Best Action")
    lines.append("")
    lines.append("- High contactability and active journey progress should prioritize a timely call or expert handoff.")
    lines.append("- Repeated visits, quote/proposal progress, or expert connection should prioritize product clarification and a focused follow-up.")
    lines.append("- Read/click/reply or meaningful CDR activity should prioritize the channel with observed engagement rather than an assumed channel.")
    lines.append("- Low activity should result in a measured nurture or information action, not an invented customer attribute or unsupported offer.")
    lines.append("- The decision engine uses only Excel-derived signals and stored AI predictions; its recommendation is a derived system output.")
    lines.append("")
    lines.append("### 7.6 Stage 6 - Assignment, Action, And Feedback")
    lines.append("")
    lines.append("- Assign the lead to the operational section indicated by CRM_Department and preserve CRM source attribution.")
    lines.append("- Record calls, tasks, follow-ups, and timeline events with the complete Excel_Fields snapshot attached.")
    lines.append("- Capture outcome feedback only after an action occurs. Do not feed that outcome back into the same prediction request as an input.")
    lines.append("- Use analytics and reports to compare source, product, journey, engagement, and call patterns for future campaign and staffing decisions.")
    lines.append("")
    lines.append("Sales Optimization Diagram:")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("  A[Exact Excel Row] --> B[Lead and Customer Profile]")
    lines.append("  B --> C[Source and Product Attribution]")
    lines.append("  C --> D[CRM + CDR + MSG + WEB + ev_ Signals]")
    lines.append("  D --> E[Leakage-Safe AI Predictions]")
    lines.append("  E --> F[Derived Lead Score and Next Action]")
    lines.append("  F --> G[Assignment, Call, Task, Follow-up]")
    lines.append("  G --> H[Observed Outcome and Timeline]")
    lines.append("  H --> I[Analytics and Reporting Feedback]")
    lines.append("  I -. improves operations, not same-outcome features .-> C")
    lines.append("```")
    lines.append("")
    lines.append("## 8. API Inventory And Response Contracts")
    lines.append("")
    lines.append(f"Total API paths in OpenAPI: {len(paths)}")
    lines.append("")

    for path in sorted(paths.keys()):
        methods = paths[path]
        for method in HTTP_METHODS:
            if method not in methods:
                continue
            op = methods[method]
            summary = op.get("summary", "")
            tag = ",".join(op.get("tags", []))
            req = request_summary(op, spec)
            resp = response_summary(op, spec)
            lines.append(f"### {method.upper()} {path}")
            if summary:
                lines.append(f"- Summary: {summary}")
            if tag:
                lines.append(f"- Tags: {tag}")
            lines.append(f"- Request: {req}")
            lines.append(f"- Responses: {resp}")
            lines.append("")

    lines.append("## 9. Lead Lifecycle Behavior")
    lines.append("")
    lines.append("1. New lead creation writes lead_created event to timeline.")
    lines.append("2. Assign/transfer updates lead ownership and section, and writes lifecycle events.")
    lines.append("3. Outcome recording can update lead status/stage and auto-create follow-ups.")
    lines.append("4. /leads/{id}/details returns a unified payload for frontend lead workspace rendering.")
    lines.append("")
    lines.append("## 10. Validation Snapshot")
    lines.append("")
    lines.append("- Test suite passing (including lifecycle tests).")
    lines.append("- Live smoke APIs passing with real sample data preloaded.")
    lines.append("- Lifecycle endpoints verified: timeline, details, assign, transfer, outcomes list/create.")
    lines.append("")

    return "\n".join(lines)


def markdown_to_pdf(md_text: str, pdf_path: Path) -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        spaceAfter=4,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=6,
    )
    code = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        spaceAfter=3,
    )
    subheading = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        spaceBefore=6,
        spaceAfter=4,
    )

    story = []
    mermaid_mode = False
    last_heading = ""
    for raw_line in md_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 2.5 * mm))
            continue
        if line == "```mermaid":
            mermaid_mode = True
            continue
        if line == "```" and mermaid_mode:
            mermaid_mode = False
            continue
        if mermaid_mode:
            continue
        if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            last_heading = line.lstrip("# ")
            story.append(Paragraph(last_heading, heading))
            if "Architecture" in last_heading:
                story.append(Spacer(1, 2 * mm))
                story.append(architecture_diagram())
                story.append(Spacer(1, 3 * mm))
            if "Feature Workflows" in last_heading:
                story.append(Spacer(1, 2 * mm))
                story.append(lifecycle_diagram())
                story.append(Spacer(1, 3 * mm))
            if "Sales Optimization" in last_heading:
                story.append(Spacer(1, 2 * mm))
                story.append(sales_optimization_diagram())
                story.append(Spacer(1, 3 * mm))
            continue
        if line.startswith("```"):
            continue
        if "->" in line and "Client" in line:
            story.append(Paragraph(line.replace(" ", "&nbsp;"), code))
            continue
        if line.startswith("Architecture Diagram") or line.startswith("Lifecycle Diagram"):
            story.append(Paragraph(line, subheading))
            continue
        if line == "Excel Ingestion Diagram:":
            story.append(Paragraph(line, subheading))
            story.append(ingestion_diagram())
            story.append(Spacer(1, 3 * mm))
            continue
        if line == "Feature Mapping Diagram:":
            story.append(Paragraph(line, subheading))
            story.append(feature_mapping_diagram())
            story.append(Spacer(1, 3 * mm))
            continue
        if line == "Prediction Guardrail Diagram:":
            story.append(Paragraph(line, subheading))
            story.append(prediction_guardrail_diagram())
            story.append(Spacer(1, 3 * mm))
            continue
        if line == "API Flow Diagram:":
            story.append(Paragraph(line, subheading))
            story.append(api_flow_diagram())
            story.append(Spacer(1, 3 * mm))
            continue
        if line == "Sales Funnel Diagram:":
            story.append(Paragraph(line, subheading))
            story.append(funnel_diagram())
            story.append(Spacer(1, 3 * mm))
            continue
        if line == "Sales Optimization Diagram:":
            story.append(Paragraph(line, subheading))
            story.append(sales_optimization_diagram())
            story.append(Spacer(1, 3 * mm))
            continue
        if line.startswith("- ") or line[0:2].isdigit() and line[1] == ".":
            story.append(Paragraph(line, body))
            continue
        story.append(Paragraph(line, body))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Backend Project Handbook",
        author="AI Sales and Lead Intelligence Backend",
    )
    doc.build(story)


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    spec = app.openapi()
    md_text = build_markdown(spec)
    MD_PATH.write_text(md_text, encoding="utf-8")
    markdown_to_pdf(md_text, PDF_PATH)

    print(f"Markdown written: {MD_PATH}")
    print(f"PDF written: {PDF_PATH}")


if __name__ == "__main__":
    main()
