import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ai_repository import AIRepository
from app.core.excel_contract import LEAKAGE_COLUMNS, source_features
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
            model_name="excel_field_baseline",
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
            return {"excel_fields": {}, "feature_columns": [], "prediction_point": datetime.now(UTC).isoformat()}

        lead = self.repository.get_lead(db, lead_id)
        if lead is None:
            return {"excel_fields": {}, "feature_columns": [], "prediction_point": datetime.now(UTC).isoformat()}

        fields = source_features(lead.excel_fields)
        customer = self.repository.get_customer(db, lead.customer_id)
        if customer is not None:
            customer_fields = source_features(customer.excel_fields)
            for column, value in customer_fields.items():
                fields.setdefault(column, value)
        return {
            "excel_fields": fields,
            "feature_columns": sorted(fields),
            "prediction_point": datetime.now(UTC).isoformat(),
            "excluded_columns": sorted(LEAKAGE_COLUMNS),
        }

    def _score_from_baseline(self, features: dict) -> float:
        fields = features.get("excel_fields", {})
        connect_rate = self._number(fields.get("CDR_Connect_Rate"))
        page_views = self._number(fields.get("Page_Views"))
        message_engagement = self._number(fields.get("MSG_Engaged"))
        web_tracked = self._number(fields.get("WEB_Tracked"))
        event_activity = sum(self._number(value) for key, value in fields.items() if key.startswith("ev_"))

        score = connect_rate * 0.35
        score += min(page_views / 30.0, 1.0) * 0.25
        score += min(message_engagement / 20.0, 1.0) * 0.15
        score += min(web_tracked / 10.0, 1.0) * 0.10
        score += min(event_activity / 20.0, 1.0) * 0.15
        return max(0.0, min(1.0, score))

    def _shape_prediction(self, prediction_type: str, score: float, features: dict) -> tuple[str, str, dict]:
        if prediction_type == "validity":
            label = "valid" if score >= 0.35 else "suspect"
            rationale = "Customer validity was scored from pre-outcome Excel fields; LABEL_Customer_Validity was excluded as the target."
        elif prediction_type == "intent":
            label = "high_intent" if score >= 0.6 else "medium_intent" if score >= 0.35 else "low_intent"
            rationale = "Intent estimated from canonical CRM, CDR, MSG, WEB, and ev_ fields available at prediction time."
        elif prediction_type == "conversion":
            label = "likely_convert" if score >= 0.55 else "needs_nurture"
            rationale = "Conversion estimated from pre-outcome Excel fields; outcome and label columns were excluded from inputs."
        elif prediction_type == "product-recommendation":
            fields = features.get("excel_fields", {})
            label = "product_match" if fields.get("WEB_Plan_Type") or fields.get("CRM_Product_Code") or fields.get("CRM_Product_Name") else "product_unavailable"
            rationale = "Product recommendation uses only CRM product and WEB product fields from Excel."
        elif prediction_type == "lead-score":
            label = "A" if score >= 0.7 else "B" if score >= 0.45 else "C"
            rationale = "Derived lead score calculated only from canonical pre-outcome CRM, CDR, MSG, WEB, and ev_ fields."
        elif prediction_type == "segment":
            label = "hot" if score >= 0.65 else "warm" if score >= 0.35 else "cold"
            rationale = "Segmentation computed from canonical customer, engagement, call, website, and event fields."
        elif prediction_type == "next-best-action":
            label = "call_now" if score >= 0.6 else "send_nurture_message"
            rationale = "Suggested action generated from Excel-derived engagement and conversion signals."
        else:
            label = "unknown"
            rationale = "Prediction type not recognized."

        target_column = {
            "validity": "LABEL_Customer_Validity",
            "conversion": "Label_Source_Lead_Status",
        }.get(prediction_type)
        return label, rationale, {
            "features": features,
            "score_band": label,
            "target_column": target_column,
            "derived_output": True,
        }

    @staticmethod
    def _number(value: object) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

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
