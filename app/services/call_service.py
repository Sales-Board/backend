from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.call import Call
from app.models.customer import Customer
from app.models.lead import Lead
from app.repositories.call_repository import CallRepository
from app.schemas.call import CallCreate, CallEndRequest, CallStartRequest, CallUpdate


class CallService:
    def __init__(self, repository: CallRepository | None = None) -> None:
        self.repository = repository or CallRepository()

    def list_calls(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        lead_id: int | None = None,
        customer_id: int | None = None,
        status_filter: str | None = None,
    ) -> list[Call]:
        return self.repository.list(
            db,
            skip=skip,
            limit=limit,
            lead_id=lead_id,
            customer_id=customer_id,
            status=status_filter,
        )

    def get_call(self, db: Session, call_id: int) -> Call:
        call = self.repository.get(db, call_id)
        if call is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
        return call

    def create_call(self, db: Session, payload: CallCreate) -> Call:
        self._validate_links(db, payload.lead_id, payload.customer_id)
        return self.repository.create(db, payload)

    def update_call(self, db: Session, call_id: int, payload: CallUpdate) -> Call:
        call = self.get_call(db, call_id)
        lead_id = payload.lead_id if payload.lead_id is not None else call.lead_id
        customer_id = payload.customer_id if payload.customer_id is not None else call.customer_id
        self._validate_links(db, lead_id, customer_id)
        return self.repository.update(db, call, payload)

    def delete_call(self, db: Session, call_id: int) -> None:
        call = self.get_call(db, call_id)
        self.repository.delete(db, call)

    def start_call(self, db: Session, call_id: int, payload: CallStartRequest) -> Call:
        call = self.get_call(db, call_id)
        if call.status == "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start a completed call")
        call.started_at = payload.started_at or datetime.now(UTC)
        call.status = "in_progress"
        return self.repository.persist(db, call)

    def end_call(self, db: Session, call_id: int, payload: CallEndRequest) -> Call:
        call = self.get_call(db, call_id)
        end_time = self._as_utc(payload.ended_at or datetime.now(UTC))
        start_time = self._as_utc(call.started_at or end_time)
        duration = max(0, int((end_time - start_time).total_seconds()))

        call.ended_at = end_time
        call.duration_seconds = duration
        call.status = "completed"
        if payload.notes is not None:
            call.notes = payload.notes
        return self.repository.persist(db, call)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _validate_links(self, db: Session, lead_id: int | None, customer_id: int | None) -> None:
        if lead_id is not None and db.get(Lead, lead_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_id does not exist")
        if customer_id is not None and db.get(Customer, customer_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="customer_id does not exist")
