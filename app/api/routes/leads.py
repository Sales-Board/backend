from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.lead import LeadCreate, LeadRead, LeadUpdate
from app.schemas.website_journey import WebsiteEventRead
from app.services.lead_service import LeadService
from app.services.website_journey_service import WebsiteJourneyService

router = APIRouter(prefix="/leads", tags=["leads"])
lead_service = LeadService()
journey_service = WebsiteJourneyService()


@router.get("", response_model=list[LeadRead])
def list_leads(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    customer_id: int | None = Query(default=None, ge=1),
    campaign_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[LeadRead]:
    return lead_service.list_leads(
        db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        campaign_id=campaign_id,
    )


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadRead:
    return lead_service.create_lead(db, payload)


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadRead:
    return lead_service.get_lead(db, lead_id)


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)) -> LeadRead:
    return lead_service.update_lead(db, lead_id, payload)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> Response:
    lead_service.delete_lead(db, lead_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{lead_id}/journey", response_model=list[WebsiteEventRead])
def get_lead_journey(
    lead_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[WebsiteEventRead]:
    lead_service.get_lead(db, lead_id)
    return journey_service.list_lead_journey(db, lead_id=lead_id, skip=skip, limit=limit)
