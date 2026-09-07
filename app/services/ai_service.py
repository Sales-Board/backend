import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ai_repository import AIRepository
from app.schemas.ai import AILeadAnalysisResponse, AIPredictionLogRead, AIPredictionRequest, AIPredictionResponse


class AIService:
    def __init__(self, repository: AIRepository | None = None) -> None:
        self.repository = repository or AIRepository()

    def predict(self, db: Session, prediction_type: str, payload: AIPredictionRequest) -> AIPredictionResponse:
        lead_id, customer_id = self._resolve_subject(db, payload)
        features = self._build_features(db, lead_id)
        score = self._score_from_baseline(features)

        label, rationale, details = self._shape_prediction(prediction_type, score, features)
        saved = self.repository.create_prediction(
            db,
            lead_id=lead_id,
            customer_id=customer_id,
            prediction_type=prediction_type,
            model_name="lead_conversion_baseline",
            score=score,
            label=label,
            rationale=rationale,
            details=details,
        )
        return AIPredictionResponse(
            prediction_type=saved.prediction_type,
            model_name=saved.model_name,
            score=saved.score,
            label=saved.label,
            rationale=saved.rationale or "",
            details=saved.details,
        )

    def analyze_lead(self, db: Session, payload: AIPredictionRequest) -> AILeadAnalysisResponse:
        prediction_types = [
            "validity",
            "intent",
            "conversion",
            "product-recommendation",
            "lead-score",
            "segment",
            "next-best-action",
        ]
        results = [self.predict(db, prediction_type, payload) for prediction_type in prediction_types]
        lead_id, customer_id = self._resolve_subject(db, payload)
        return AILeadAnalysisResponse(
            lead_id=lead_id,
            customer_id=customer_id,
            generated_at=datetime.now(UTC),
            predictions=results,
        )

    def get_lead_predictions(self, db: Session, lead_id: int) -> list[AIPredictionLogRead]:
        if self.repository.get_lead(db, lead_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        rows = self.repository.list_predictions_for_lead(db, lead_id)
        return [AIPredictionLogRead.model_validate(row) for row in rows]

    def get_customer_predictions(self, db: Session, customer_id: int) -> list[AIPredictionLogRead]:
        if self.repository.get_customer(db, customer_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        rows = self.repository.list_predictions_for_customer(db, customer_id)
        return [AIPredictionLogRead.model_validate(row) for row in rows]

    def _resolve_subject(self, db: Session, payload: AIPredictionRequest) -> tuple[int | None, int | None]:
        lead_id = payload.lead_id
        customer_id = payload.customer_id

        if lead_id is None and customer_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_id or customer_id is required")

        if lead_id is not None:
            lead = self.repository.get_lead(db, lead_id)
            if lead is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
            if customer_id is None:
                customer_id = lead.customer_id

        if customer_id is not None and self.repository.get_customer(db, customer_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        return lead_id, customer_id

    def _build_features(self, db: Session, lead_id: int | None) -> dict:
        if lead_id is None:
            return {"source_channel": "unknown", "priority": "medium", "call_count": 0, "engagement_count": 0}

        lead = self.repository.get_lead(db, lead_id)
        if lead is None:
            return {"source_channel": "unknown", "priority": "medium", "call_count": 0, "engagement_count": 0}

        return {
            "source_channel": lead.source_channel or "unknown",
            "priority": lead.priority or "medium",
            "call_count": self.repository.lead_call_count(db, lead_id),
            "engagement_count": self.repository.lead_engagement_count(db, lead_id),
        }

    def _score_from_baseline(self, features: dict) -> float:
        artifact = self._load_latest_artifact()
        base = float(artifact.get("global_positive_rate", 0.3))
        channel_rate = artifact.get("channel_positive_rate", {})
        priority_rate = artifact.get("priority_positive_rate", {})

        channel = features.get("source_channel", "unknown")
        priority = features.get("priority", "medium")
        channel_score = float(channel_rate.get(channel, base))
        priority_score = float(priority_rate.get(priority, base))

        behavior_boost = min(0.15, 0.02 * int(features.get("call_count", 0)) + 0.01 * int(features.get("engagement_count", 0)))
        score = (0.45 * base) + (0.25 * channel_score) + (0.25 * priority_score) + behavior_boost
        return max(0.0, min(1.0, score))

    def _shape_prediction(self, prediction_type: str, score: float, features: dict) -> tuple[str, str, dict]:
        if prediction_type == "validity":
            label = "valid" if score >= 0.35 else "suspect"
            rationale = "Lead profile consistency and engagement signals were evaluated."
        elif prediction_type == "intent":
            label = "high_intent" if score >= 0.6 else "medium_intent" if score >= 0.35 else "low_intent"
            rationale = "Intent estimated from engagement, call activity, source channel, and priority."
        elif prediction_type == "conversion":
            label = "likely_convert" if score >= 0.55 else "needs_nurture"
            rationale = "Conversion probability estimated using baseline conversion patterns."
        elif prediction_type == "product-recommendation":
            label = "protection_plan" if features.get("priority") == "high" else "wealth_plan"
            rationale = "Product recommendation based on lead urgency profile and baseline behavior."
        elif prediction_type == "lead-score":
            label = "A" if score >= 0.7 else "B" if score >= 0.45 else "C"
            rationale = "Composite lead score based on historical training artifact and activity signals."
        elif prediction_type == "segment":
            label = "hot" if score >= 0.65 else "warm" if score >= 0.35 else "cold"
            rationale = "Segmentation computed from predicted conversion tendency and engagement depth."
        elif prediction_type == "next-best-action":
            label = "call_now" if score >= 0.6 else "send_nurture_message"
            rationale = "Suggested action generated from intent/conversion score bands."
        else:
            label = "unknown"
            rationale = "Prediction type not recognized."

        return label, rationale, {"features": features, "score_band": label}

    @staticmethod
    def _load_latest_artifact() -> dict:
        artifact_dir = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
        files = sorted(artifact_dir.glob("*.json"), reverse=True)
        if not files:
            return {
                "global_positive_rate": 0.3,
                "channel_positive_rate": {},
                "priority_positive_rate": {},
            }
        return json.loads(files[0].read_text(encoding="utf-8"))
