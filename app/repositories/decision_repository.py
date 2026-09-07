from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_prediction import AIPrediction
from app.models.customer import Customer
from app.models.decision_recommendation import DecisionRecommendation
from app.models.lead import Lead


class DecisionRepository:
    def get_lead(self, db: Session, lead_id: int) -> Lead | None:
        return db.get(Lead, lead_id)

    def get_customer(self, db: Session, customer_id: int) -> Customer | None:
        return db.get(Customer, customer_id)

    def get_latest_prediction(self, db: Session, lead_id: int | None, customer_id: int | None, prediction_type: str) -> AIPrediction | None:
        stmt = select(AIPrediction).where(AIPrediction.prediction_type == prediction_type)
        if lead_id is not None:
            stmt = stmt.where(AIPrediction.lead_id == lead_id)
        elif customer_id is not None:
            stmt = stmt.where(AIPrediction.customer_id == customer_id)
        else:
            return None
        stmt = stmt.order_by(AIPrediction.id.desc()).limit(1)
        return db.scalars(stmt).first()

    def create_recommendation(
        self,
        db: Session,
        lead_id: int | None,
        customer_id: int | None,
        decision_type: str,
        recommended_action: str,
        priority: str,
        confidence: float,
        rationale: str,
        inputs: dict | None,
    ) -> DecisionRecommendation:
        row = DecisionRecommendation(
            lead_id=lead_id,
            customer_id=customer_id,
            decision_type=decision_type,
            recommended_action=recommended_action,
            priority=priority,
            confidence=confidence,
            rationale=rationale,
            inputs=inputs,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_for_lead(self, db: Session, lead_id: int, limit: int = 100) -> list[DecisionRecommendation]:
        stmt = (
            select(DecisionRecommendation)
            .where(DecisionRecommendation.lead_id == lead_id)
            .order_by(DecisionRecommendation.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def list_for_customer(self, db: Session, customer_id: int, limit: int = 100) -> list[DecisionRecommendation]:
        stmt = (
            select(DecisionRecommendation)
            .where(DecisionRecommendation.customer_id == customer_id)
            .order_by(DecisionRecommendation.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
