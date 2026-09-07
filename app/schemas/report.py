from pydantic import BaseModel


class CampaignReportItem(BaseModel):
    campaign_id: int
    campaign_code: str
    campaign_name: str
    lead_count: int
    converted_leads: int
    conversion_rate: float


class CampaignPerformanceReportResponse(BaseModel):
    items: list[CampaignReportItem]


class WorkloadReportResponse(BaseModel):
    total_tasks: int
    open_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    total_followups: int
    pending_followups: int
    completed_followups: int


class PipelineReportResponse(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    converted_leads: int
    lost_leads: int
