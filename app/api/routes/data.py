from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.data_management import (
    DataQualityResponse,
    DataLoadApplyRequest,
    DataLoadApplyResponse,
    DataLoadDatasetInfo,
    DataLoadPreviewResponse,
    DataLoadRequest,
    ExportRequest,
    ExportResponse,
    ImportJobRead,
    ImportJobRequest,
    ValidationResponse,
)
from app.services.data_service import DataService
from app.services.data_load_service import DataLoadService

router = APIRouter(prefix="/data", tags=["data"])
data_service = DataService()
data_load_service = DataLoadService()


@router.get("/load/datasets", response_model=list[DataLoadDatasetInfo])
def list_load_datasets() -> list[DataLoadDatasetInfo]:
    return data_load_service.list_datasets()


@router.post("/load/preview", response_model=DataLoadPreviewResponse)
def preview_data_load(payload: DataLoadRequest, db: Session = Depends(get_db)) -> DataLoadPreviewResponse:
    return data_load_service.preview(db, payload)


@router.post("/load/apply", response_model=DataLoadApplyResponse, status_code=status.HTTP_201_CREATED)
def apply_data_load(payload: DataLoadApplyRequest, db: Session = Depends(get_db)) -> DataLoadApplyResponse:
    return data_load_service.apply(db, payload)


@router.post("/import", response_model=ImportJobRead, status_code=status.HTTP_201_CREATED)
def import_data(payload: ImportJobRequest, db: Session = Depends(get_db)) -> ImportJobRead:
    return data_service.import_data(db, payload)


@router.get("/import/{job_id}", response_model=ImportJobRead)
def get_import_job(job_id: int, db: Session = Depends(get_db)) -> ImportJobRead:
    return data_service.get_import_job(db, job_id)


@router.get("/quality", response_model=DataQualityResponse)
def get_data_quality(db: Session = Depends(get_db)) -> DataQualityResponse:
    return data_service.get_quality_report(db)


@router.get("/validation", response_model=ValidationResponse)
def get_data_validation(db: Session = Depends(get_db)) -> ValidationResponse:
    return data_service.get_validation_report(db)


@router.get("/history", response_model=list[ImportJobRead])
def get_data_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ImportJobRead]:
    return data_service.list_history(db, skip=skip, limit=limit)


@router.post("/export", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
def export_data(payload: ExportRequest, db: Session = Depends(get_db)) -> ExportResponse:
    return data_service.export_data(db, payload)
