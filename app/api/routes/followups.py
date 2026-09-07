from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.task_followup import FollowupCreate, FollowupRead, FollowupUpdate
from app.services.followup_service import FollowupService

router = APIRouter(prefix="/followups", tags=["followups"])
followup_service = FollowupService()


@router.get("", response_model=list[FollowupRead])
def list_followups(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    task_id: int | None = Query(default=None, ge=1),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[FollowupRead]:
    return followup_service.list_followups(
        db,
        skip=skip,
        limit=limit,
        task_id=task_id,
        lead_id=lead_id,
        customer_id=customer_id,
    )


@router.post("", response_model=FollowupRead, status_code=status.HTTP_201_CREATED)
def create_followup(payload: FollowupCreate, db: Session = Depends(get_db)) -> FollowupRead:
    return followup_service.create_followup(db, payload)


@router.patch("/{followup_id}", response_model=FollowupRead)
def update_followup(followup_id: int, payload: FollowupUpdate, db: Session = Depends(get_db)) -> FollowupRead:
    return followup_service.update_followup(db, followup_id, payload)
