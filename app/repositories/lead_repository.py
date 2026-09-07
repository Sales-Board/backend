from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadRepository:
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        customer_id: int | None = None,
        campaign_id: int | None = None,
    ) -> list[Lead]:
        stmt = select(Lead).order_by(Lead.id).offset(skip).limit(limit)
        if customer_id is not None:
            stmt = stmt.where(Lead.customer_id == customer_id)
        if campaign_id is not None:
            stmt = stmt.where(Lead.campaign_id == campaign_id)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, lead_id: int) -> Lead | None:
        return db.get(Lead, lead_id)

    def create(self, db: Session, payload: LeadCreate) -> Lead:
        lead = Lead(**payload.model_dump())
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    def update(self, db: Session, lead: Lead, payload: LeadUpdate) -> Lead:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(lead, field, value)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    def delete(self, db: Session, lead: Lead) -> None:
        db.delete(lead)
        db.commit()
