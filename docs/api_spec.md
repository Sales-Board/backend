# API Specification (Initial)

## Base

- Unversioned support for `/health`
- Versioned support for `/api/*`

## Health

1. `GET /health`
2. `GET /api/health`

## Dashboard

1. `GET /api/dashboard`

## Leads

Status: Implemented base CRUD endpoints, lead journey endpoint, and lead calls endpoint (timeline/engagement/ai pending).

1. `GET /api/leads`
2. `POST /api/leads`
3. `GET /api/leads/{id}`
4. `PATCH /api/leads/{id}`
5. `DELETE /api/leads/{id}`
6. `GET /api/leads/{id}/timeline`
7. `GET /api/leads/{id}/engagement`
8. `GET /api/leads/{id}/journey`
9. `GET /api/leads/{id}/calls`
10. `GET /api/leads/{id}/ai`
11. `POST /api/leads/{id}/assign`
12. `POST /api/leads/{id}/transfer`

## Customers

Status: Implemented CRUD endpoints.

1. `GET /api/customers`
2. `POST /api/customers`
3. `GET /api/customers/{id}`
4. `PATCH /api/customers/{id}`
5. `DELETE /api/customers/{id}`
6. `GET /api/customers/{id}/timeline`
7. `GET /api/customers/{id}/leads`

## Products

Status: Implemented CRUD endpoints.

1. `GET /api/products`
2. `POST /api/products`
3. `GET /api/products/{id}`
4. `PATCH /api/products/{id}`
5. `DELETE /api/products/{id}`

## Campaigns

Status: Implemented CRUD, campaign leads, and campaign performance endpoints.

1. `GET /api/campaigns`
2. `POST /api/campaigns`
3. `GET /api/campaigns/{id}`
4. `PATCH /api/campaigns/{id}`
5. `DELETE /api/campaigns/{id}`
6. `GET /api/campaigns/{id}/leads`
7. `GET /api/campaigns/{id}/performance`

## Engagement

Status: Implemented channel query endpoints.

1. `GET /api/engagement/whatsapp`
2. `GET /api/engagement/rcs`
3. `GET /api/engagement/email`
4. `GET /api/engagement/website`

## Website Journey

Status: Implemented website journey query and lead journey summary endpoints.

1. `GET /api/journey/website`
2. `GET /api/journey/leads/{lead_id}`

## Calls

Status: Implemented CRUD and call lifecycle endpoints.

1. `GET /api/calls`
2. `POST /api/calls`
3. `GET /api/calls/{id}`
4. `PATCH /api/calls/{id}`
5. `POST /api/calls/{id}/start`
6. `POST /api/calls/{id}/end`

## AI

Status: Implemented all AI prediction endpoints with baseline artifact-backed scoring and prediction logs.

1. `POST /api/ai/validity`
2. `POST /api/ai/intent`
3. `POST /api/ai/conversion`
4. `POST /api/ai/product-recommendation`
5. `POST /api/ai/lead-score`
6. `POST /api/ai/segment`
7. `POST /api/ai/next-best-action`
8. `POST /api/ai/analyze-lead`
9. `GET /api/ai/leads/{id}`
10. `GET /api/ai/customers/{id}`

## Decision Engine

Status: Implemented next-action recommendations and decision log retrieval endpoints.

1. `POST /api/decision/next-action`
2. `GET /api/decision/leads/{id}`
3. `GET /api/decision/customers/{id}`

## ML Pipeline

Status: Implemented baseline training pipeline and model registry endpoints.

1. `POST /api/ml/train`
2. `GET /api/ml/train/{job_id}`
3. `GET /api/ml/models`

## Tasks and Followups

1. `GET /api/tasks`
2. `POST /api/tasks`
3. `GET /api/tasks/{id}`
4. `PATCH /api/tasks/{id}`
5. `DELETE /api/tasks/{id}`
6. `GET /api/followups`
7. `POST /api/followups`
8. `PATCH /api/followups/{id}`

## Analytics and Reports

1. `GET /api/analytics/*`
2. `GET /api/reports/*`

## Data Management

Status: Implemented import profiling jobs, job lookup, quality report, validation report, history, and export endpoints.

1. `POST /api/data/import`
2. `GET /api/data/import/{job_id}`
3. `GET /api/data/quality`
4. `GET /api/data/validation`
5. `GET /api/data/history`
6. `POST /api/data/export`
