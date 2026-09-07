from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.models.ml_training_job import MLTrainingJob


class MLRepository:
    def create_job(self, db: Session, model_name: str) -> MLTrainingJob:
        job = MLTrainingJob(model_name=model_name, status="processing")
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def complete_job(self, db: Session, job: MLTrainingJob, training_rows: int, metrics: dict, artifact_path: str) -> MLTrainingJob:
        job.status = "completed"
        job.training_rows = training_rows
        job.metrics = metrics
        job.artifact_path = artifact_path
        job.completed_at = datetime.now(UTC)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def fail_job(self, db: Session, job: MLTrainingJob, message: str) -> MLTrainingJob:
        job.status = "failed"
        job.error_message = message
        job.completed_at = datetime.now(UTC)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def get_job(self, db: Session, job_id: int) -> MLTrainingJob | None:
        return db.get(MLTrainingJob, job_id)

    def list_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> list[MLTrainingJob]:
        stmt = select(MLTrainingJob).order_by(MLTrainingJob.id.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def list_latest_jobs_grouped(self, db: Session) -> list[MLTrainingJob]:
        subquery = (
            select(MLTrainingJob.model_name, func.max(MLTrainingJob.id).label("latest_id"))
            .group_by(MLTrainingJob.model_name)
            .subquery()
        )
        stmt = (
            select(MLTrainingJob)
            .join(subquery, MLTrainingJob.id == subquery.c.latest_id)
            .order_by(MLTrainingJob.model_name.asc())
        )
        return list(db.scalars(stmt).all())

    def fetch_training_rows(self, db: Session) -> list[dict]:
        stmt = select(Lead.id, Lead.excel_fields)

        rows: list[dict] = []
        for lead_id, excel_fields in db.execute(stmt).all():
            fields = excel_fields or {}
            rows.append(
                {
                    "lead_id": int(lead_id),
                    "excel_fields": fields,
                    "target": fields.get("Label_Source_Lead_Status"),
                }
            )
        return rows
