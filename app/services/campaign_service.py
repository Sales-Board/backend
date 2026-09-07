from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.lead import Lead
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignPerformance, CampaignUpdate


class CampaignService:
    def __init__(self, repository: CampaignRepository | None = None) -> None:
        self.repository = repository or CampaignRepository()

    def list_campaigns(self, db: Session, skip: int = 0, limit: int = 100) -> list[Campaign]:
        return self.repository.list(db, skip=skip, limit=limit)

    def get_campaign(self, db: Session, campaign_id: int) -> Campaign:
        campaign = self.repository.get(db, campaign_id)
        if campaign is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        return campaign

    def create_campaign(self, db: Session, payload: CampaignCreate) -> Campaign:
        try:
            return self.repository.create(db, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="campaign code must be unique",
            ) from exc

    def update_campaign(self, db: Session, campaign_id: int, payload: CampaignUpdate) -> Campaign:
        campaign = self.get_campaign(db, campaign_id)
        try:
            return self.repository.update(db, campaign, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="campaign code must be unique",
            ) from exc

    def delete_campaign(self, db: Session, campaign_id: int) -> None:
        campaign = self.get_campaign(db, campaign_id)
        self.repository.delete(db, campaign)

    def list_campaign_leads(self, db: Session, campaign_id: int, skip: int = 0, limit: int = 100) -> list[Lead]:
        self.get_campaign(db, campaign_id)
        return self.repository.list_leads(db, campaign_id, skip=skip, limit=limit)

    def get_campaign_performance(self, db: Session, campaign_id: int) -> CampaignPerformance:
        self.get_campaign(db, campaign_id)
        by_channel_items = self.repository.count_events_by_channel(db, campaign_id)
        by_metric_items = self.repository.count_events_by_metric(db, campaign_id)
        by_channel = {key: value for key, value in by_channel_items}
        by_metric = {key: value for key, value in by_metric_items}
        total = sum(by_channel.values())
        return CampaignPerformance(
            campaign_id=campaign_id,
            total_events=total,
            by_channel=by_channel,
            by_metric=by_metric,
        )
