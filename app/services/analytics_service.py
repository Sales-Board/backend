from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsChannelsResponse, AnalyticsFunnelResponse, AnalyticsOverviewResponse, ChannelAnalyticsItem


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository | None = None) -> None:
        self.repository = repository or AnalyticsRepository()

    def get_overview(self, db) -> AnalyticsOverviewResponse:
        payload = self.repository.fetch_overview(db)
        total_leads = payload["total_leads"]
        converted = payload["converted_leads"]
        conversion_rate = round((converted / total_leads), 4) if total_leads > 0 else 0.0
        return AnalyticsOverviewResponse(
            **payload,
            conversion_rate=conversion_rate,
        )

    def get_funnel(self, db) -> AnalyticsFunnelResponse:
        counts = self.repository.fetch_funnel_status_counts(db)
        new_leads = counts.get("new", 0)
        qualified_leads = counts.get("qualified", 0)
        converted_leads = counts.get("converted", 0)
        lost_leads = counts.get("lost", 0)
        total_leads = sum(counts.values())
        conversion_rate = round((converted_leads / total_leads), 4) if total_leads > 0 else 0.0
        return AnalyticsFunnelResponse(
            new_leads=new_leads,
            qualified_leads=qualified_leads,
            converted_leads=converted_leads,
            lost_leads=lost_leads,
            total_leads=total_leads,
            conversion_rate=conversion_rate,
        )

    def get_channels(self, db) -> AnalyticsChannelsResponse:
        items = [ChannelAnalyticsItem(**item) for item in self.repository.fetch_channel_analytics(db)]
        return AnalyticsChannelsResponse(items=items)
