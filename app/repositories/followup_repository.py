from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.followup import Followup
from app.schemas.task_followup import FollowupCreate, FollowupUpdate


class FollowupRepository:
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        task_id: int | None = None,
        lead_id: int | None = None,
        customer_id: int | None = None,
    ) -> list[Followup]:
        stmt = select(Followup).order_by(Followup.id).offset(skip).limit(limit)
        if task_id is not None:
            stmt = stmt.where(Followup.task_id == task_id)
        if lead_id is not None:
            stmt = stmt.where(Followup.lead_id == lead_id)
        if customer_id is not None:
            stmt = stmt.where(Followup.customer_id == customer_id)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, followup_id: int) -> Followup | None:
        return db.get(Followup, followup_id)

    def create(self, db: Session, payload: FollowupCreate) -> Followup:
        row = Followup(**payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update(self, db: Session, followup: Followup, payload: FollowupUpdate) -> Followup:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(followup, field, value)
        db.add(followup)
        db.commit()
        db.refresh(followup)
        return followup
