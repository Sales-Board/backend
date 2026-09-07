# AI Sales and Lead Intelligence Backend

Modular FastAPI backend for a sales and lead intelligence platform where lead lifecycle is the core business object.

## Current Status

Step 1 complete: project foundation, API bootstrap, health endpoint, and dataset/domain planning docs.
Step 2 complete: PostgreSQL + SQLAlchemy + Alembic foundation with DB-aware health checks.
Step 3 complete: Customer domain with full CRUD APIs, persistence model, migration, and tests.
Step 4 complete: Lead domain with base CRUD APIs, persistence model, migration, and tests.

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
│   │   │   ├── customers.py
│   │   │   ├── health.py
│   │   │   └── leads.py
│   │   └── router.py
│   ├── models/
│   │   ├── customer.py
│   │   └── lead.py
│   ├── repositories/
│   │   ├── customer_repository.py
│   │   └── lead_repository.py
│   ├── services/
│   │   ├── customer_service.py
│   │   └── lead_service.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── schemas/
│   │   ├── customer.py
│   │   ├── health.py
│   │   └── lead.py
│   └── main.py
├── docs/
│   ├── api_spec.md
│   ├── data_assessment.md
│   └── schema_proposal.md
├── tests/
│   ├── test_customers.py
│   ├── test_health.py
│   └── test_leads.py
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
5. Product Domain
6. Campaign + Engagement
7. Website/Event Journey
8. Calls
9. Data Import Pipeline
10. ML Pipeline
11. AI Prediction APIs
12. Decision Engine
13. Tasks / Follow-ups
14. Analytics
15. Reports
16. Integration Testing
17. Performance Optimization

