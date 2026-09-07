from sqlalchemy.orm import Session

from app.models.engagement_event import EngagementEvent
from app.repositories.engagement_repository import EngagementRepository


class EngagementService:
    def __init__(self, repository: EngagementRepository | None = None) -> None:
        self.repository = repository or EngagementRepository()

    def list_events_by_channel(
        self,
        db: Session,
        channel: str,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        campaign_id: int | None = None,
    ) -> list[EngagementEvent]:
        return self.repository.list_by_channel(
            db,
            channel=channel,
            skip=skip,
            limit=limit,
            lead_id=lead_id,
            customer_id=customer_id,
            campaign_id=campaign_id,
        )
