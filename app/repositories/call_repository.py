from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.call import Call
from app.schemas.call import CallCreate, CallUpdate


class CallRepository:
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        status: str | None = None,
    ) -> list[Call]:
        stmt = select(Call).order_by(Call.id).offset(skip).limit(limit)
        if lead_id is not None:
            stmt = stmt.where(Call.lead_id == lead_id)
        if customer_id is not None:
            stmt = stmt.where(Call.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Call.status == status)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, call_id: int) -> Call | None:
        return db.get(Call, call_id)

    def create(self, db: Session, payload: CallCreate) -> Call:
        call = Call(**payload.model_dump())
        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    def update(self, db: Session, call: Call, payload: CallUpdate) -> Call:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(call, field, value)
        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    def persist(self, db: Session, call: Call) -> Call:
        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    def delete(self, db: Session, call: Call) -> None:
        db.delete(call)
        db.commit()
