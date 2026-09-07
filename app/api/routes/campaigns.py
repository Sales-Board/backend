from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.campaign import CampaignCreate, CampaignPerformance, CampaignRead, CampaignUpdate
from app.schemas.lead import LeadRead
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
campaign_service = CampaignService()


@router.get("", response_model=list[CampaignRead])
def list_campaigns(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[CampaignRead]:
    return campaign_service.list_campaigns(db, skip=skip, limit=limit)


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> CampaignRead:
    return campaign_service.create_campaign(db, payload)


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)) -> CampaignRead:
    return campaign_service.get_campaign(db, campaign_id)


@router.patch("/{campaign_id}", response_model=CampaignRead)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
) -> CampaignRead:
    return campaign_service.update_campaign(db, campaign_id, payload)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)) -> Response:
    campaign_service.delete_campaign(db, campaign_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{campaign_id}/leads", response_model=list[LeadRead])
def list_campaign_leads(
    campaign_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[LeadRead]:
    return campaign_service.list_campaign_leads(db, campaign_id, skip=skip, limit=limit)


@router.get("/{campaign_id}/performance", response_model=CampaignPerformance)
def get_campaign_performance(campaign_id: int, db: Session = Depends(get_db)) -> CampaignPerformance:
    return campaign_service.get_campaign_performance(db, campaign_id)
