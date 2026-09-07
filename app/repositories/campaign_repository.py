from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.engagement_event import EngagementEvent
from app.models.lead import Lead
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignRepository:
    def list(self, db: Session, skip: int = 0, limit: int = 100) -> list[Campaign]:
        stmt = select(Campaign).order_by(Campaign.id).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, campaign_id: int) -> Campaign | None:
        return db.get(Campaign, campaign_id)

    def create(self, db: Session, payload: CampaignCreate) -> Campaign:
        campaign = Campaign(**payload.model_dump())
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    def update(self, db: Session, campaign: Campaign, payload: CampaignUpdate) -> Campaign:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(campaign, field, value)
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    def delete(self, db: Session, campaign: Campaign) -> None:
        db.delete(campaign)
        db.commit()

    def list_leads(self, db: Session, campaign_id: int, skip: int = 0, limit: int = 100) -> list[Lead]:
        stmt = select(Lead).where(Lead.campaign_id == campaign_id).order_by(Lead.id).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def count_events_by_channel(self, db: Session, campaign_id: int) -> list[tuple[str, int]]:
        stmt = (
            select(EngagementEvent.channel, func.count(EngagementEvent.id))
            .where(EngagementEvent.campaign_id == campaign_id)
            .group_by(EngagementEvent.channel)
        )
        return [(row[0], int(row[1])) for row in db.execute(stmt).all()]

    def count_events_by_metric(self, db: Session, campaign_id: int) -> list[tuple[str, int]]:
        stmt = (
            select(EngagementEvent.metric_type, func.count(EngagementEvent.id))
            .where(EngagementEvent.campaign_id == campaign_id)
            .group_by(EngagementEvent.metric_type)
        )
        return [(row[0], int(row[1])) for row in db.execute(stmt).all()]
