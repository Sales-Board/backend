from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.call import Call
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.data_import_job import DataImportJob
from app.models.engagement_event import EngagementEvent
from app.models.lead import Lead
from app.models.product import Product
from app.models.website_event import WebsiteEvent


class DataRepository:
    def create_import_job(self, db: Session, dataset_name: str, source_path: str) -> DataImportJob:
        job = DataImportJob(dataset_name=dataset_name, source_path=source_path, status="processing")
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def complete_import_job(
        self,
        db: Session,
        job: DataImportJob,
        row_count: int,
        valid_row_count: int,
        invalid_row_count: int,
        details: dict | None = None,
    ) -> DataImportJob:
        job.status = "completed"
        job.row_count = row_count
        job.valid_row_count = valid_row_count
        job.invalid_row_count = invalid_row_count
        job.details = details
        job.completed_at = datetime.now(UTC)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def fail_import_job(self, db: Session, job: DataImportJob, error_message: str) -> DataImportJob:
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(UTC)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def get_import_job(self, db: Session, job_id: int) -> DataImportJob | None:
        return db.get(DataImportJob, job_id)

    def list_import_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> list[DataImportJob]:
        stmt = select(DataImportJob).order_by(DataImportJob.id.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def table_counts(self, db: Session) -> dict[str, int]:
        return {
            "customers": int(db.scalar(select(func.count(Customer.id))) or 0),
            "leads": int(db.scalar(select(func.count(Lead.id))) or 0),
            "products": int(db.scalar(select(func.count(Product.id))) or 0),
            "campaigns": int(db.scalar(select(func.count(Campaign.id))) or 0),
            "calls": int(db.scalar(select(func.count(Call.id))) or 0),
            "engagement_events": int(db.scalar(select(func.count(EngagementEvent.id))) or 0),
            "website_events": int(db.scalar(select(func.count(WebsiteEvent.id))) or 0),
            "import_jobs": int(db.scalar(select(func.count(DataImportJob.id))) or 0),
        }

    def completed_calls_missing_duration(self, db: Session) -> int:
        stmt = select(func.count(Call.id)).where(Call.status == "completed", Call.duration_seconds.is_(None))
        return int(db.scalar(stmt) or 0)

    def completed_calls_count(self, db: Session) -> int:
        stmt = select(func.count(Call.id)).where(Call.status == "completed")
        return int(db.scalar(stmt) or 0)

    def calls_with_end_before_start(self, db: Session) -> int:
        stmt = select(func.count(Call.id)).where(
            Call.started_at.is_not(None),
            Call.ended_at.is_not(None),
            Call.ended_at < Call.started_at,
        )
        return int(db.scalar(stmt) or 0)

    def customers_missing_external_id(self, db: Session) -> int:
        stmt = select(func.count(Customer.id)).where(Customer.external_customer_id == "")
        return int(db.scalar(stmt) or 0)

    def fetch_resource_rows(self, db: Session, resource: str, limit: int = 10000) -> list[dict]:
        model_map = {
            "customers": Customer,
            "leads": Lead,
            "products": Product,
            "campaigns": Campaign,
            "calls": Call,
            "engagement_events": EngagementEvent,
            "website_events": WebsiteEvent,
            "import_jobs": DataImportJob,
        }
        model = model_map.get(resource)
        if model is None:
            return []

        stmt = select(model).limit(limit)
        rows = db.scalars(stmt).all()
        serialized: list[dict] = []
        for row in rows:
            item: dict = {}
            for column in model.__table__.columns:  # type: ignore[attr-defined]
                value = getattr(row, column.name)
                if isinstance(value, datetime):
                    item[column.name] = value.isoformat()
                else:
                    item[column.name] = value
            serialized.append(item)
        return serialized
