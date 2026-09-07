from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.website_event import WebsiteEvent


class WebsiteJourneyRepository:
    def list_events(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        device_type: str | None = None,
    ) -> list[WebsiteEvent]:
        stmt = select(WebsiteEvent).order_by(WebsiteEvent.event_time.desc()).offset(skip).limit(limit)
        if lead_id is not None:
            stmt = stmt.where(WebsiteEvent.lead_id == lead_id)
        if customer_id is not None:
            stmt = stmt.where(WebsiteEvent.customer_id == customer_id)
        if device_type is not None:
            stmt = stmt.where(WebsiteEvent.device_type == device_type)
        return list(db.scalars(stmt).all())

    def list_lead_events(self, db: Session, lead_id: int, skip: int = 0, limit: int = 100) -> list[WebsiteEvent]:
        stmt = (
            select(WebsiteEvent)
            .where(WebsiteEvent.lead_id == lead_id)
            .order_by(WebsiteEvent.event_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
