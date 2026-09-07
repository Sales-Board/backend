from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    # Database integration is added in Step 2.
    return HealthResponse(status="ok", database="not_configured")
