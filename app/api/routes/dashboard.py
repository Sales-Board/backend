from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["dashboard"])
analytics_service = AnalyticsService()


@router.get("/dashboard", response_model=AnalyticsOverviewResponse)
def get_dashboard(db: Session = Depends(get_db)) -> AnalyticsOverviewResponse:
    return analytics_service.get_overview(db)
