from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.ai import AILeadAnalysisResponse, AIPredictionLogRead, AIPredictionRequest, AIPredictionResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = AIService()


@router.post("/validity", response_model=AIPredictionResponse)
def predict_validity(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "validity", payload)


@router.post("/intent", response_model=AIPredictionResponse)
def predict_intent(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "intent", payload)


@router.post("/conversion", response_model=AIPredictionResponse)
def predict_conversion(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "conversion", payload)


@router.post("/product-recommendation", response_model=AIPredictionResponse)
def predict_product(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "product-recommendation", payload)


@router.post("/lead-score", response_model=AIPredictionResponse)
def predict_lead_score(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "lead-score", payload)


@router.post("/segment", response_model=AIPredictionResponse)
def predict_segment(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "segment", payload)


@router.post("/next-best-action", response_model=AIPredictionResponse)
def predict_next_action(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AIPredictionResponse:
    return ai_service.predict(db, "next-best-action", payload)


@router.post("/analyze-lead", response_model=AILeadAnalysisResponse)
def analyze_lead(payload: AIPredictionRequest, db: Session = Depends(get_db)) -> AILeadAnalysisResponse:
    return ai_service.analyze_lead(db, payload)


@router.get("/leads/{lead_id}", response_model=list[AIPredictionLogRead])
def get_lead_predictions(lead_id: int, db: Session = Depends(get_db)) -> list[AIPredictionLogRead]:
    return ai_service.get_lead_predictions(db, lead_id)


@router.get("/customers/{customer_id}", response_model=list[AIPredictionLogRead])
def get_customer_predictions(customer_id: int, db: Session = Depends(get_db)) -> list[AIPredictionLogRead]:
    return ai_service.get_customer_predictions(db, customer_id)
