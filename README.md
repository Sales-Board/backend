# AI Sales and Lead Intelligence Backend

FastAPI backend for lead-centric workflow automation, analytics, AI scoring, and decision support.

## What Is Implemented

1. Health and dashboard APIs.
2. Customer, lead, product, campaign CRUD domains.
3. Engagement, website journey, calls, tasks, and follow-up workflows.
4. Data import/export and quality validation APIs.
5. ML training and model catalog APIs.
6. AI prediction and decision recommendation APIs.
7. Analytics and reporting APIs.
8. Lead lifecycle operations:
	 - Assignment and transfer.
	 - Timeline event tracking.
	 - Outcome capture and follow-up generation.
	 - Unified lead details response.

## Architecture

- `app/api/routes/*`: HTTP contracts and endpoint registration.
- `app/services/*`: business workflow orchestration.
- `app/repositories/*`: DB query and persistence layer.
- `app/models/*`: SQLAlchemy models.
- `app/schemas/*`: Pydantic request/response contracts.
- `app/db/migrations/*`: Alembic schema evolution.

Request flow:

```text
Client -> FastAPI Route -> Service -> Repository -> PostgreSQL
																		-> Domain logic -> Response schema
```

## Local Setup (Backend-Only, venv Inside backend)

From project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional ML extras:

```bash
pip install -r requirements-ml.txt
```

Create env file:

```bash
cp .env.example .env
```

## PostgreSQL Setup

Use local PostgreSQL and ensure database `lead_intelligence` exists.

Ubuntu helper:

```bash
./scripts/setup_postgres_ubuntu.sh
```

Apply migrations:

```bash
./.venv/bin/alembic upgrade head
```

## Load Real Sample Data

This imports real records from `backend/sample_data.xlsx` (sheet: `dataset`).

```bash
./.venv/bin/python scripts/preload_sample_data.py --reset
```

Optional custom path:

```bash
./.venv/bin/python scripts/preload_sample_data.py --reset --dataset-path ./sample_data.xlsx
```

Important dataset metadata:

- Column definitions are read from `sample_data.xlsx` and mapped into product/campaign/customer/lead/call/task/follow-up/engagement/website entities.
- Dataset dictionary sheet (`data_dictionary`) is included in generated handbook documentation.

## Run API Server

```bash
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Docs URLs

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## Validate APIs End-to-End

1. Automated smoke checks:

```bash
./.venv/bin/python scripts/live_api_smoke.py
```

2. Test suite:

```bash
./.venv/bin/pytest -q
```

3. Lifecycle test coverage:

```bash
./.venv/bin/pytest -q tests/test_lead_lifecycle.py
```

## Lifecycle API Surface

All endpoints are under `/api` prefix.

- `GET /leads/{lead_id}/timeline`
	- Returns chronological lifecycle events.
- `GET /leads/{lead_id}/details`
	- Returns unified payload: lead, customer, campaign, engagement, journey, AI block, calls, tasks, followups, outcomes, timeline.
- `POST /leads/{lead_id}/assign`
	- Assigns lead to a section/handler.
- `POST /leads/{lead_id}/transfer`
	- Transfers lead to a new section/handler.
- `POST /leads/{lead_id}/outcomes`
	- Records action outcome and can auto-create follow-up.
- `GET /leads/{lead_id}/outcomes`
	- Lists outcome history.

## Data Processing Flow

1. Data import API records import jobs and metadata.
2. Preload script maps real sample dataset into core entities (products, campaigns, customers, leads).
3. Service layer creates linked operational records (tasks, followups, calls, engagement, journey events).
4. AI endpoints generate prediction logs per lead.
5. Decision endpoints generate next-action recommendations.
6. Lifecycle layer combines outcomes, assignments, and events into a single lead timeline and details view.

## Docker Mode

```bash
cp .env.docker.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Docs (Docker):

- `http://localhost:8000/api/docs`

## Generate Full Project Handbook PDF

Generate a full technical handbook (features, architecture, API inventory, data flow, lifecycle behavior):

```bash
./.venv/bin/pip install reportlab
./.venv/bin/python scripts/generate_project_docs_pdf.py
```

Outputs:

- `docs/project_backend_handbook.md`
- `docs/project_backend_handbook.pdf`

The handbook includes:

- Architecture and lifecycle diagrams.
- Detailed runbook.
- API request/response parameters.
- Full `sample_data.xlsx` column list and column dictionary mapping.

## Quick Troubleshooting

- `404 /openapi.json`: use `/api/openapi.json`.
- DB connection errors: verify `DATABASE_URL` in `.env` and PostgreSQL service status.
- Empty API lists: run preload command with `--reset`.

