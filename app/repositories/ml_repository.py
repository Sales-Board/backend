from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.call import Call
from app.models.engagement_event import EngagementEvent
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
        call_counts = (
            select(Call.lead_id, func.count(Call.id).label("call_count"))
            .where(Call.lead_id.is_not(None))
            .group_by(Call.lead_id)
            .subquery()
        )
        engagement_counts = (
            select(EngagementEvent.lead_id, func.count(EngagementEvent.id).label("engagement_count"))
            .where(EngagementEvent.lead_id.is_not(None))
            .group_by(EngagementEvent.lead_id)
            .subquery()
        )

        stmt = (
            select(
                Lead.id,
                Lead.source_channel,
                Lead.priority,
                Lead.status,
                func.coalesce(call_counts.c.call_count, 0),
                func.coalesce(engagement_counts.c.engagement_count, 0),
            )
            .outerjoin(call_counts, call_counts.c.lead_id == Lead.id)
            .outerjoin(engagement_counts, engagement_counts.c.lead_id == Lead.id)
        )

        rows: list[dict] = []
        for lead_id, source_channel, priority, status, call_count, engagement_count in db.execute(stmt).all():
            rows.append(
                {
                    "lead_id": int(lead_id),
                    "source_channel": source_channel or "unknown",
                    "priority": priority or "unknown",
                    "status": status or "new",
                    "call_count": int(call_count or 0),
                    "engagement_count": int(engagement_count or 0),
                }
            )
        return rows
