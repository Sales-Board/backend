from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.decision import DecisionLogRead, DecisionRequest, DecisionResponse
from app.services.ai_service import AIService
from app.repositories.decision_repository import DecisionRepository


class DecisionService:
    def __init__(self, repository: DecisionRepository | None = None, ai_service: AIService | None = None) -> None:
        self.repository = repository or DecisionRepository()
        self.ai_service = ai_service or AIService()

    def decide_next_action(self, db: Session, payload: DecisionRequest) -> DecisionResponse:
        lead_id, customer_id = self._resolve_subject(db, payload)

        intent = self.repository.get_latest_prediction(db, lead_id, customer_id, "intent")
        conversion = self.repository.get_latest_prediction(db, lead_id, customer_id, "conversion")
        next_action = self.repository.get_latest_prediction(db, lead_id, customer_id, "next-best-action")

        if intent is None:
            intent = self.ai_service.predict(db, "intent", self._to_ai_payload(lead_id, customer_id))
        if conversion is None:
            conversion = self.ai_service.predict(db, "conversion", self._to_ai_payload(lead_id, customer_id))
        if next_action is None:
            next_action = self.ai_service.predict(db, "next-best-action", self._to_ai_payload(lead_id, customer_id))

        intent_score = float(intent.score if hasattr(intent, "score") else intent.score)
        conversion_score = float(conversion.score if hasattr(conversion, "score") else conversion.score)
        nbo_label = next_action.label

        confidence = max(0.0, min(1.0, (intent_score + conversion_score) / 2.0))
        if confidence >= 0.7:
            priority = "high"
            action = "assign_senior_agent_and_call_now"
        elif confidence >= 0.45:
            priority = "medium"
            action = "schedule_callback_and_share_brochure"
        else:
            priority = "low"
            action = "nurture_sequence_email_whatsapp"

        if nbo_label == "call_now":
            action = "assign_senior_agent_and_call_now"
            priority = "high" if confidence >= 0.5 else "medium"

        rationale = "Decision combines latest intent, conversion, and next-best-action predictions."
        inputs = {
            "intent_score": intent_score,
            "conversion_score": conversion_score,
            "next_best_action_label": nbo_label,
        }

        row = self.repository.create_recommendation(
            db,
            lead_id=lead_id,
            customer_id=customer_id,
            decision_type="next_action",
            recommended_action=action,
            priority=priority,
            confidence=confidence,
            rationale=rationale,
            inputs=inputs,
        )

        return DecisionResponse(
            decision_type=row.decision_type,
            recommended_action=row.recommended_action,
            priority=row.priority,
            confidence=row.confidence,
            rationale=row.rationale,
            inputs=row.inputs,
        )

    def get_lead_decisions(self, db: Session, lead_id: int) -> list[DecisionLogRead]:
        if self.repository.get_lead(db, lead_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return [DecisionLogRead.model_validate(row) for row in self.repository.list_for_lead(db, lead_id)]

    def get_customer_decisions(self, db: Session, customer_id: int) -> list[DecisionLogRead]:
        if self.repository.get_customer(db, customer_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return [DecisionLogRead.model_validate(row) for row in self.repository.list_for_customer(db, customer_id)]

    def _resolve_subject(self, db: Session, payload: DecisionRequest) -> tuple[int | None, int | None]:
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

    @staticmethod
    def _to_ai_payload(lead_id: int | None, customer_id: int | None):
        from app.schemas.ai import AIPredictionRequest

        return AIPredictionRequest(lead_id=lead_id, customer_id=customer_id)
