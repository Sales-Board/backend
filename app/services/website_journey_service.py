from sqlalchemy.orm import Session

from app.models.website_event import WebsiteEvent
from app.repositories.website_journey_repository import WebsiteJourneyRepository
from app.schemas.website_journey import JourneySummary


class WebsiteJourneyService:
    def __init__(self, repository: WebsiteJourneyRepository | None = None) -> None:
        self.repository = repository or WebsiteJourneyRepository()

    def list_events(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        device_type: str | None = None,
    ) -> list[WebsiteEvent]:
        return self.repository.list_events(
            db,
            skip=skip,
            limit=limit,
            lead_id=lead_id,
            customer_id=customer_id,
            device_type=device_type,
        )

    def list_lead_journey(self, db: Session, lead_id: int, skip: int = 0, limit: int = 100) -> list[WebsiteEvent]:
        return self.repository.list_lead_events(db, lead_id, skip=skip, limit=limit)

    def get_lead_journey_summary(self, db: Session, lead_id: int) -> JourneySummary:
        events = self.repository.list_lead_events(db, lead_id=lead_id, skip=0, limit=1000)
        unique_names = sorted({event.event_name for event in events})
        last_event_time = events[0].event_time if events else None
        return JourneySummary(
            lead_id=lead_id,
            total_events=len(events),
            unique_event_names=unique_names,
            last_event_time=last_event_time,
        )
