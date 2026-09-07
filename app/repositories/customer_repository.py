from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerRepository:
    def list(self, db: Session, skip: int = 0, limit: int = 100) -> list[Customer]:
        stmt = select(Customer).offset(skip).limit(limit).order_by(Customer.id)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, customer_id: int) -> Customer | None:
        return db.get(Customer, customer_id)

    def create(self, db: Session, payload: CustomerCreate) -> Customer:
        customer = Customer(**payload.model_dump())
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    def update(self, db: Session, customer: Customer, payload: CustomerUpdate) -> Customer:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    def delete(self, db: Session, customer: Customer) -> None:
        db.delete(customer)
        db.commit()
