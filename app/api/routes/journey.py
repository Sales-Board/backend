from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.website_journey import JourneySummary, WebsiteEventRead
from app.services.lead_service import LeadService
from app.services.website_journey_service import WebsiteJourneyService

router = APIRouter(prefix="/journey", tags=["journey"])
journey_service = WebsiteJourneyService()
lead_service = LeadService()


@router.get("/website", response_model=list[WebsiteEventRead])
def list_website_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    device_type: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
) -> list[WebsiteEventRead]:
    return journey_service.list_events(
        db,
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        device_type=device_type,
    )


@router.get("/leads/{lead_id}", response_model=JourneySummary)
def get_lead_journey_summary(lead_id: int, db: Session = Depends(get_db)) -> JourneySummary:
    lead_service.get_lead(db, lead_id)
    return journey_service.get_lead_journey_summary(db, lead_id)
