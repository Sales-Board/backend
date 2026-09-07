from fastapi import APIRouter

from app.api.routes.customers import router as customers_router
from app.api.routes.health import router as health_router
from app.api.routes.leads import router as leads_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health_router)

v1_router = APIRouter(prefix=settings.api_prefix)
v1_router.include_router(health_router)
v1_router.include_router(customers_router)
v1_router.include_router(leads_router)
api_router.include_router(v1_router)
