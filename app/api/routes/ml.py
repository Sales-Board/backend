from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.ml import MLModelSummary, MLTrainingJobRead, MLTrainRequest
from app.services.ml_service import MLService

router = APIRouter(prefix="/ml", tags=["ml"])
ml_service = MLService()


@router.post("/train", response_model=MLTrainingJobRead, status_code=status.HTTP_201_CREATED)
def train_model(payload: MLTrainRequest, db: Session = Depends(get_db)) -> MLTrainingJobRead:
    return ml_service.train(db, payload)


@router.get("/train/{job_id}", response_model=MLTrainingJobRead)
def get_training_job(job_id: int, db: Session = Depends(get_db)) -> MLTrainingJobRead:
    return ml_service.get_job(db, job_id)


@router.get("/models", response_model=list[MLModelSummary])
def list_models(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[MLModelSummary]:
    models = ml_service.list_models(db)
    return models[skip : skip + limit]
