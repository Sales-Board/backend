# AI Sales and Lead Intelligence Backend

Modular FastAPI backend for a sales and lead intelligence platform where lead lifecycle is the core business object.

## Current Status

Step 1 complete: project foundation, API bootstrap, health endpoint, and dataset/domain planning docs.
Step 2 complete: PostgreSQL + SQLAlchemy + Alembic foundation with DB-aware health checks.
Step 3 complete: Customer domain with full CRUD APIs, persistence model, migration, and tests.
Step 4 complete: Lead domain with base CRUD APIs, persistence model, migration, and tests.
Step 5 complete: Product domain with full CRUD APIs, persistence model, migration, and tests.
Step 6 complete: Campaign + Engagement domain with campaign CRUD, campaign lead/performance APIs, engagement channel APIs, migration, and tests.
Step 7 complete: Website/Event Journey domain with lead journey endpoint, journey query APIs, migration, and tests.
Step 8 complete: Calls domain with CRUD, start/end lifecycle APIs, lead calls endpoint, migration, and tests.
Step 9 complete: Data Import Pipeline with import job tracking, data quality/validation reports, history, export API, migration, and tests.
Step 10 complete: ML Pipeline with baseline model training, training-job tracking, model listing APIs, migration, and tests.
Step 11 complete: AI Prediction APIs with baseline scoring, full endpoint surface, prediction logs, migration, and tests.
Step 12 complete: Decision Engine with next-action recommendations, decision logs, migration, and tests.
Step 13 complete: Tasks and Follow-ups with task CRUD, follow-up scheduling/update APIs, migration, and tests.

## Tech Stack

- Python 3.12+
- FastAPI
- Pydantic v2
- Uvicorn
- pytest + httpx
- PostgreSQL, SQLAlchemy, Alembic

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Optional ML stack (later roadmap steps):

```bash
pip install -r requirements-ml.txt
```

3. Copy environment file:

```bash
cp .env.example .env
```

4. Start server:

```bash
uvicorn app.main:app --reload
```

## API Docs

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Health Check

```http
GET /health
```

Response:

```json
{
	"status": "ok",
	"database": "connected | unavailable | not_configured"
}
```

## Database & Migrations

1. Ensure PostgreSQL is running (local or Docker).
2. Set `DATABASE_URL` in `.env`.
3. Run migrations:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe_change"
```

## Tests

```bash
pytest -q
```

## Implemented Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── campaigns.py
│   │   │   ├── calls.py
│   │   │   ├── customers.py
│   │   │   ├── data.py
│   │   │   ├── engagement.py
│   │   │   ├── health.py
│   │   │   ├── journey.py
│   │   │   ├── leads.py
│   │   │   └── products.py
│   │   └── router.py
│   ├── models/
│   │   ├── call.py
│   │   ├── campaign.py
│   │   ├── customer.py
│   │   ├── data_import_job.py
│   │   ├── engagement_event.py
│   │   ├── lead.py
│   │   ├── product.py
│   │   └── website_event.py
│   ├── repositories/
│   │   ├── call_repository.py
│   │   ├── campaign_repository.py
│   │   ├── customer_repository.py
│   │   ├── data_repository.py
│   │   ├── engagement_repository.py
│   │   ├── lead_repository.py
│   │   ├── product_repository.py
│   │   └── website_journey_repository.py
│   ├── services/
│   │   ├── call_service.py
│   │   ├── campaign_service.py
│   │   ├── customer_service.py
│   │   ├── data_service.py
│   │   ├── engagement_service.py
│   │   ├── lead_service.py
│   │   ├── product_service.py
│   │   └── website_journey_service.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── schemas/
│   │   ├── call.py
│   │   ├── campaign.py
│   │   ├── customer.py
│   │   ├── data_management.py
│   │   ├── engagement.py
│   │   ├── health.py
│   │   ├── lead.py
│   │   ├── product.py
│   │   └── website_journey.py
│   └── main.py
├── docs/
│   ├── api_spec.md
│   ├── data_assessment.md
│   └── schema_proposal.md
├── tests/
│   ├── test_calls.py
│   ├── test_campaigns.py
│   ├── test_customers.py
│   ├── test_data_pipeline.py
│   ├── test_engagement.py
│   ├── test_health.py
│   ├── test_journey.py
│   ├── test_leads.py
│   └── test_products.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Roadmap (Incremental)

1. Project Foundation (done)
2. PostgreSQL + SQLAlchemy + Alembic (done)
3. Customer Domain (done)
4. Lead Domain (done)
5. Product Domain (done)
6. Campaign + Engagement (done)
7. Website/Event Journey (done)
8. Calls (done)
9. Data Import Pipeline (done)
10. ML Pipeline (done)
11. AI Prediction APIs (done)
12. Decision Engine (done)
13. Tasks / Follow-ups (done)
14. Analytics
15. Reports
16. Integration Testing
17. Performance Optimization

