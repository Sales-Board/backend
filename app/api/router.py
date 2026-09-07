from fastapi import APIRouter

from app.api.routes.ai import router as ai_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.calls import router as calls_router
from app.api.routes.customers import router as customers_router
from app.api.routes.data import router as data_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.decision import router as decision_router
from app.api.routes.engagement import router as engagement_router
from app.api.routes.followups import router as followups_router
from app.api.routes.health import router as health_router
from app.api.routes.journey import router as journey_router
from app.api.routes.leads import router as leads_router
from app.api.routes.ml import router as ml_router
from app.api.routes.products import router as products_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health_router)

v1_router = APIRouter(prefix=settings.api_prefix)
v1_router.include_router(health_router)
v1_router.include_router(customers_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(leads_router)
v1_router.include_router(products_router)
v1_router.include_router(ai_router)
v1_router.include_router(analytics_router)
v1_router.include_router(campaigns_router)
v1_router.include_router(calls_router)
v1_router.include_router(data_router)
v1_router.include_router(decision_router)
v1_router.include_router(engagement_router)
v1_router.include_router(followups_router)
v1_router.include_router(journey_router)
v1_router.include_router(ml_router)
v1_router.include_router(tasks_router)
api_router.include_router(v1_router)
