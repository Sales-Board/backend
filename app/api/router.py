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
from app.api.routes.reports import router as reports_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings

public_router = APIRouter()
public_router.include_router(health_router)

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health_router)
api_router.include_router(customers_router)
api_router.include_router(dashboard_router)
api_router.include_router(leads_router)
api_router.include_router(products_router)
api_router.include_router(ai_router)
api_router.include_router(analytics_router)
api_router.include_router(campaigns_router)
api_router.include_router(calls_router)
api_router.include_router(data_router)
api_router.include_router(decision_router)
api_router.include_router(engagement_router)
api_router.include_router(followups_router)
api_router.include_router(journey_router)
api_router.include_router(ml_router)
api_router.include_router(reports_router)
api_router.include_router(tasks_router)
