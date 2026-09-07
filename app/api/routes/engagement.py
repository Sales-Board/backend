from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.engagement import EngagementEventRead
from app.services.engagement_service import EngagementService

router = APIRouter(prefix="/engagement", tags=["engagement"])
engagement_service = EngagementService()


@router.get("/whatsapp", response_model=list[EngagementEventRead])
def list_whatsapp_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    campaign_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[EngagementEventRead]:
    return engagement_service.list_events_by_channel(
        db,
        channel="whatsapp",
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        campaign_id=campaign_id,
    )


@router.get("/rcs", response_model=list[EngagementEventRead])
def list_rcs_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    campaign_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[EngagementEventRead]:
    return engagement_service.list_events_by_channel(
        db,
        channel="rcs",
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        campaign_id=campaign_id,
    )


@router.get("/email", response_model=list[EngagementEventRead])
def list_email_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    campaign_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[EngagementEventRead]:
    return engagement_service.list_events_by_channel(
        db,
        channel="email",
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        campaign_id=campaign_id,
    )


@router.get("/website", response_model=list[EngagementEventRead])
def list_website_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    lead_id: int | None = Query(default=None, ge=1),
    customer_id: int | None = Query(default=None, ge=1),
    campaign_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[EngagementEventRead]:
    return engagement_service.list_events_by_channel(
        db,
        channel="website",
        skip=skip,
        limit=limit,
        lead_id=lead_id,
        customer_id=customer_id,
        campaign_id=campaign_id,
    )
