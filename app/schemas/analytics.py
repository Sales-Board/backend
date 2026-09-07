from pydantic import BaseModel


class AnalyticsOverviewResponse(BaseModel):
    total_customers: int
    total_leads: int
    total_campaigns: int
    total_calls: int
    open_tasks: int
    pending_followups: int
    converted_leads: int
    conversion_rate: float


class AnalyticsFunnelResponse(BaseModel):
    new_leads: int
    qualified_leads: int
    converted_leads: int
    lost_leads: int
    total_leads: int
    conversion_rate: float


class ChannelAnalyticsItem(BaseModel):
    channel: str
    lead_count: int
    engagement_events: int


class AnalyticsChannelsResponse(BaseModel):
    items: list[ChannelAnalyticsItem]
