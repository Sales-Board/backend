from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task_followup import TaskCreate, TaskUpdate


class TaskRepository:
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        status_filter: str | None = None,
    ) -> list[Task]:
        stmt = select(Task).order_by(Task.id).offset(skip).limit(limit)
        if lead_id is not None:
            stmt = stmt.where(Task.lead_id == lead_id)
        if customer_id is not None:
            stmt = stmt.where(Task.customer_id == customer_id)
        if status_filter is not None:
            stmt = stmt.where(Task.status == status_filter)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, task_id: int) -> Task | None:
        return db.get(Task, task_id)

    def create(self, db: Session, payload: TaskCreate) -> Task:
        row = Task(**payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update(self, db: Session, task: Task, payload: TaskUpdate) -> Task:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db: Session, task: Task) -> None:
        db.delete(task)
        db.commit()
