from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engagement_event import EngagementEvent


class EngagementRepository:
    def list_by_channel(
        self,
        db: Session,
        channel: str,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        campaign_id: int | None = None,
    ) -> list[EngagementEvent]:
        stmt = (
            select(EngagementEvent)
            .where(EngagementEvent.channel == channel)
            .order_by(EngagementEvent.event_time.desc())
            .offset(skip)
            .limit(limit)
        )
        if lead_id is not None:
            stmt = stmt.where(EngagementEvent.lead_id == lead_id)
        if customer_id is not None:
            stmt = stmt.where(EngagementEvent.customer_id == customer_id)
        if campaign_id is not None:
            stmt = stmt.where(EngagementEvent.campaign_id == campaign_id)
        return list(db.scalars(stmt).all())
