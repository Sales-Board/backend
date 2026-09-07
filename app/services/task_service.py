from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.lead import Lead
from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task_followup import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository | None = None) -> None:
        self.repository = repository or TaskRepository()

    def list_tasks(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        status_filter: str | None = None,
    ) -> list[Task]:
        return self.repository.list(
            db,
            skip=skip,
            limit=limit,
            lead_id=lead_id,
            customer_id=customer_id,
            status_filter=status_filter,
        )

    def get_task(self, db: Session, task_id: int) -> Task:
        row = self.repository.get(db, task_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return row

    def create_task(self, db: Session, payload: TaskCreate) -> Task:
        self._validate_links(db, payload.lead_id, payload.customer_id)
        return self.repository.create(db, payload)

    def update_task(self, db: Session, task_id: int, payload: TaskUpdate) -> Task:
        row = self.get_task(db, task_id)
        lead_id = payload.lead_id if payload.lead_id is not None else row.lead_id
        customer_id = payload.customer_id if payload.customer_id is not None else row.customer_id
        self._validate_links(db, lead_id, customer_id)
        return self.repository.update(db, row, payload)

    def delete_task(self, db: Session, task_id: int) -> None:
        row = self.get_task(db, task_id)
        self.repository.delete(db, row)

    @staticmethod
    def _validate_links(db: Session, lead_id: int | None, customer_id: int | None) -> None:
        if lead_id is not None and db.get(Lead, lead_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_id does not exist")
        if customer_id is not None and db.get(Customer, customer_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="customer_id does not exist")
