from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.call import CallCreate, CallEndRequest, CallRead, CallStartRequest, CallUpdate
from app.services.call_service import CallService

router = APIRouter(prefix="/calls", tags=["calls"])
call_service = CallService()


@router.get("", response_model=list[CallRead])
def list_calls(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    status_filter: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CallRead]:
    return call_service.list_calls(
        db,
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        status_filter=status_filter,
    )


@router.post("", response_model=CallRead, status_code=status.HTTP_201_CREATED)
def create_call(payload: CallCreate, db: Session = Depends(get_db)) -> CallRead:
    return call_service.create_call(db, payload)


@router.get("/{call_id}", response_model=CallRead)
def get_call(call_id: int, db: Session = Depends(get_db)) -> CallRead:
    return call_service.get_call(db, call_id)


@router.patch("/{call_id}", response_model=CallRead)
def update_call(call_id: int, payload: CallUpdate, db: Session = Depends(get_db)) -> CallRead:
    return call_service.update_call(db, call_id, payload)


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call(call_id: int, db: Session = Depends(get_db)) -> Response:
    call_service.delete_call(db, call_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{call_id}/start", response_model=CallRead)
def start_call(call_id: int, payload: CallStartRequest, db: Session = Depends(get_db)) -> CallRead:
    return call_service.start_call(db, call_id, payload)


@router.post("/{call_id}/end", response_model=CallRead)
def end_call(call_id: int, payload: CallEndRequest, db: Session = Depends(get_db)) -> CallRead:
    return call_service.end_call(db, call_id, payload)
