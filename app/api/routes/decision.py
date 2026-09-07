from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.decision import DecisionLogRead, DecisionRequest, DecisionResponse
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decision", tags=["decision"])
decision_service = DecisionService()


@router.post("/next-action", response_model=DecisionResponse)
def decide_next_action(payload: DecisionRequest, db: Session = Depends(get_db)) -> DecisionResponse:
    return decision_service.decide_next_action(db, payload)


@router.get("/leads/{lead_id}", response_model=list[DecisionLogRead])
def get_lead_decisions(lead_id: int, db: Session = Depends(get_db)) -> list[DecisionLogRead]:
    return decision_service.get_lead_decisions(db, lead_id)


@router.get("/customers/{customer_id}", response_model=list[DecisionLogRead])
def get_customer_decisions(customer_id: int, db: Session = Depends(get_db)) -> list[DecisionLogRead]:
    return decision_service.get_customer_decisions(db, customer_id)
