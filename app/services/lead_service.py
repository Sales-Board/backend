from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.lead import Lead
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
    ) -> list[Lead]:
        return self.repository.list(db, skip=skip, limit=limit, customer_id=customer_id)

    def get_lead(self, db: Session, lead_id: int) -> Lead:
        lead = self.repository.get(db, lead_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return lead

    def create_lead(self, db: Session, payload: LeadCreate) -> Lead:
        self._assert_customer_exists(db, payload.customer_id)
        return self.repository.create(db, payload)

    def update_lead(self, db: Session, lead_id: int, payload: LeadUpdate) -> Lead:
        lead = self.get_lead(db, lead_id)
        if payload.customer_id is not None:
            self._assert_customer_exists(db, payload.customer_id)
        return self.repository.update(db, lead, payload)

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
