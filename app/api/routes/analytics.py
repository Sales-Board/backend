from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.analytics import AnalyticsChannelsResponse, AnalyticsFunnelResponse, AnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_service = AnalyticsService()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> AnalyticsOverviewResponse:
    return analytics_service.get_overview(db)


@router.get("/funnel", response_model=AnalyticsFunnelResponse)
def get_funnel(db: Session = Depends(get_db)) -> AnalyticsFunnelResponse:
    return analytics_service.get_funnel(db)


@router.get("/channels", response_model=AnalyticsChannelsResponse)
def get_channels(db: Session = Depends(get_db)) -> AnalyticsChannelsResponse:
    return analytics_service.get_channels(db)
