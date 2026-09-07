from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, repository: CustomerRepository | None = None) -> None:
        self.repository = repository or CustomerRepository()

    def list_customers(self, db: Session, skip: int = 0, limit: int = 100) -> list[Customer]:
        return self.repository.list(db, skip=skip, limit=limit)

    def get_customer(self, db: Session, customer_id: int) -> Customer:
        customer = self.repository.get(db, customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    def create_customer(self, db: Session, payload: CustomerCreate) -> Customer:
        try:
            return self.repository.create(db, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="external_customer_id must be unique",
            ) from exc

    def update_customer(self, db: Session, customer_id: int, payload: CustomerUpdate) -> Customer:
        customer = self.get_customer(db, customer_id)
        try:
            return self.repository.update(db, customer, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="external_customer_id must be unique",
            ) from exc

    def delete_customer(self, db: Session, customer_id: int) -> None:
        customer = self.get_customer(db, customer_id)
        self.repository.delete(db, customer)
