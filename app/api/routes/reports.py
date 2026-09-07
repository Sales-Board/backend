from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.report import CampaignPerformanceReportResponse, PipelineReportResponse, WorkloadReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
report_service = ReportService()


@router.get("/campaign-performance", response_model=CampaignPerformanceReportResponse)
def get_campaign_performance(db: Session = Depends(get_db)) -> CampaignPerformanceReportResponse:
    return report_service.get_campaign_performance(db)


@router.get("/workload", response_model=WorkloadReportResponse)
def get_workload(db: Session = Depends(get_db)) -> WorkloadReportResponse:
    return report_service.get_workload(db)


@router.get("/pipeline", response_model=PipelineReportResponse)
def get_pipeline(db: Session = Depends(get_db)) -> PipelineReportResponse:
    return report_service.get_pipeline(db)
