from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.lead_timeline_event import LeadTimelineEvent
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadService:
    def __init__(self, repository: LeadRepository | None = None) -> None:
        self.repository = repository or LeadRepository()

    def list_leads(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        customer_id: int | None = None,
        campaign_id: int | None = None,
    ) -> list[Lead]:
        return self.repository.list(
            db,
            skip=skip,
            limit=limit,
            customer_id=customer_id,
            campaign_id=campaign_id,
        )

    def get_lead(self, db: Session, lead_id: int) -> Lead:
        lead = self.repository.get(db, lead_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return lead

    def create_lead(self, db: Session, payload: LeadCreate) -> Lead:
        self._assert_customer_exists(db, payload.customer_id)
        if payload.campaign_id is not None:
            self._assert_campaign_exists(db, payload.campaign_id)
        lead = self.repository.create(db, payload)
        db.add(
            LeadTimelineEvent(
                lead_id=lead.id,
                customer_id=lead.customer_id,
                event_type="lead_created",
                event_source="lead_service",
                details={
                    "status": lead.status,
                    "current_stage": lead.current_stage,
                    "campaign_id": lead.campaign_id,
                    "source_channel": lead.source_channel,
                },
            )
        )
        db.commit()
        return lead

    def update_lead(self, db: Session, lead_id: int, payload: LeadUpdate) -> Lead:
        lead = self.get_lead(db, lead_id)
        if payload.customer_id is not None:
            self._assert_customer_exists(db, payload.customer_id)
        if payload.campaign_id is not None:
            self._assert_campaign_exists(db, payload.campaign_id)
        updated = self.repository.update(db, lead, payload)
        db.add(
            LeadTimelineEvent(
                lead_id=updated.id,
                customer_id=updated.customer_id,
                event_type="lead_updated",
                event_source="lead_service",
                details=payload.model_dump(exclude_unset=True),
            )
        )
        db.commit()
        return updated

    def delete_lead(self, db: Session, lead_id: int) -> None:
        lead = self.get_lead(db, lead_id)
        self.repository.delete(db, lead)

    def _assert_customer_exists(self, db: Session, customer_id: int) -> None:
        customer = db.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="customer_id does not exist",
            )

    def _assert_campaign_exists(self, db: Session, campaign_id: int) -> None:
        campaign = db.get(Campaign, campaign_id)
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="campaign_id does not exist",
            )
