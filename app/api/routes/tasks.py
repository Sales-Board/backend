from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.task_followup import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])
task_service = TaskService()


@router.get("", response_model=list[TaskRead])
def list_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    status_filter: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    return task_service.list_tasks(
        db,
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        status_filter=status_filter,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    return task_service.create_task(db, payload)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    return task_service.get_task(db, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskRead:
    return task_service.update_task(db, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    task_service.delete_task(db, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
