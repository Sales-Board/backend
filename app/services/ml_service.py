import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ml_repository import MLRepository
from app.core.excel_contract import LEAKAGE_COLUMNS, PRE_OUTCOME_FEATURE_COLUMNS
from app.schemas.ml import MLModelSummary, MLTrainingJobRead, MLTrainRequest


class MLService:
    def __init__(self, repository: MLRepository | None = None) -> None:
        self.repository = repository or MLRepository()

    def train(self, db: Session, payload: MLTrainRequest) -> MLTrainingJobRead:
        job = self.repository.create_job(db, payload.model_name)
        try:
            rows = self.repository.fetch_training_rows(db)
            if len(rows) < 3:
                raise ValueError("at least 3 leads are required to train baseline model")

            artifact = self._build_baseline_artifact(payload.model_name, rows)
            artifact_path = self._write_artifact(payload.model_name, artifact)
            completed = self.repository.complete_job(
                db,
                job,
                training_rows=len(rows),
                metrics=artifact["metrics"],
                artifact_path=artifact_path,
            )
            return MLTrainingJobRead.model_validate(completed)
        except Exception as exc:
            failed = self.repository.fail_job(db, job, str(exc))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=failed.error_message) from exc

    def get_job(self, db: Session, job_id: int) -> MLTrainingJobRead:
        job = self.repository.get_job(db, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML training job not found")
        return MLTrainingJobRead.model_validate(job)

    def list_models(self, db: Session) -> list[MLModelSummary]:
        jobs = self.repository.list_latest_jobs_grouped(db)
        return [
            MLModelSummary(
                model_name=job.model_name,
                latest_job_id=job.id,
                status=job.status,
                training_rows=job.training_rows,
                created_at=job.created_at,
            )
            for job in jobs
        ]

    @staticmethod
    def _build_baseline_artifact(model_name: str, rows: list[dict]) -> dict:
        positive_status = {"qualified", "converted", "interested", "follow up", "follow_up"}
        total = len(rows)
        positives = sum(1 for row in rows if str(row.get("target") or "").lower() in positive_status)
        global_rate = positives / total if total else 0.0

        return {
            "model_name": model_name,
            "created_at": datetime.now(UTC).isoformat(),
            "target": "Label_Source_Lead_Status",
            "features": list(PRE_OUTCOME_FEATURE_COLUMNS),
            "excluded_leakage_columns": sorted(LEAKAGE_COLUMNS),
            "global_positive_rate": global_rate,
            "metrics": {
                "training_rows": total,
                "positive_rows": positives,
                "global_positive_rate": global_rate,
            },
        }

    @staticmethod
    def _write_artifact(model_name: str, artifact: dict) -> str:
        artifact_dir = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = artifact_dir / f"{model_name}_{stamp}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(artifact, handle, ensure_ascii=True, indent=2)
        return str(path)
