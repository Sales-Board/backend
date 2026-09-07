from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.followup import Followup
from app.models.lead import Lead
from app.models.task import Task
from app.repositories.followup_repository import FollowupRepository
from app.schemas.task_followup import FollowupCreate, FollowupUpdate


class FollowupService:
    def __init__(self, repository: FollowupRepository | None = None) -> None:
        self.repository = repository or FollowupRepository()

    def list_followups(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        task_id: int | None = None,
        lead_id: int | None = None,
        customer_id: int | None = None,
    ) -> list[Followup]:
        return self.repository.list(
            db,
            skip=skip,
            limit=limit,
            task_id=task_id,
            lead_id=lead_id,
            customer_id=customer_id,
        )

    def get_followup(self, db: Session, followup_id: int) -> Followup:
        row = self.repository.get(db, followup_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Followup not found")
        return row

    def create_followup(self, db: Session, payload: FollowupCreate) -> Followup:
        self._validate_links(db, payload.task_id, payload.lead_id, payload.customer_id)
        return self.repository.create(db, payload)

    def update_followup(self, db: Session, followup_id: int, payload: FollowupUpdate) -> Followup:
        row = self.get_followup(db, followup_id)
        task_id = payload.task_id if payload.task_id is not None else row.task_id
        lead_id = payload.lead_id if payload.lead_id is not None else row.lead_id
        customer_id = payload.customer_id if payload.customer_id is not None else row.customer_id
        self._validate_links(db, task_id, lead_id, customer_id)

        if payload.status is not None and payload.status.lower() == "completed" and payload.completed_at is None:
            payload = payload.model_copy(update={"completed_at": datetime.now(UTC)})

        return self.repository.update(db, row, payload)

    @staticmethod
    def _validate_links(db: Session, task_id: int | None, lead_id: int | None, customer_id: int | None) -> None:
        if task_id is not None and db.get(Task, task_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task_id does not exist")
        if lead_id is not None and db.get(Lead, lead_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_id does not exist")
        if customer_id is not None and db.get(Customer, customer_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="customer_id does not exist")
