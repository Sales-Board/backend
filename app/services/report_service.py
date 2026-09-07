from sqlalchemy.orm import Session

from app.repositories.report_repository import ReportRepository
from app.schemas.report import (
    CampaignPerformanceReportResponse,
    CampaignReportItem,
    PipelineReportResponse,
    WorkloadReportResponse,
)


class ReportService:
    def __init__(self, repository: ReportRepository | None = None) -> None:
        self.repository = repository or ReportRepository()

    def get_campaign_performance(self, db: Session) -> CampaignPerformanceReportResponse:
        items = [CampaignReportItem(**row) for row in self.repository.fetch_campaign_performance(db)]
        return CampaignPerformanceReportResponse(items=items)

    def get_workload(self, db: Session) -> WorkloadReportResponse:
        return WorkloadReportResponse(**self.repository.fetch_workload(db))

    def get_pipeline(self, db: Session) -> PipelineReportResponse:
        return PipelineReportResponse(**self.repository.fetch_pipeline(db))
