# AI Sales and Lead Intelligence Backend

Modular FastAPI backend for a sales and lead intelligence platform where lead lifecycle is the core business object.

## Current Status

Step 1 complete: project foundation, API bootstrap, health endpoint, and dataset/domain planning docs.
Step 2 complete: PostgreSQL + SQLAlchemy + Alembic foundation with DB-aware health checks.

## Tech Stack

- Python 3.12+
- FastAPI
- Pydantic v2
- Uvicorn
- pytest + httpx
- PostgreSQL, SQLAlchemy, Alembic (next step)

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
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
│   │   │   └── health.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── schemas/
│   │   └── health.py
│   └── main.py
├── docs/
│   ├── api_spec.md
│   ├── data_assessment.md
│   └── schema_proposal.md
├── tests/
│   └── test_health.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Roadmap (Incremental)

1. Project Foundation (done)
2. PostgreSQL + SQLAlchemy + Alembic (done)
3. Customer Domain
4. Lead Domain
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

