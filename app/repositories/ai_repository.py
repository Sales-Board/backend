from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_prediction import AIPrediction
from app.models.call import Call
from app.models.customer import Customer
from app.models.engagement_event import EngagementEvent
from app.models.lead import Lead


class AIRepository:
    def create_prediction(
        self,
        db: Session,
        lead_id: int | None,
        customer_id: int | None,
        prediction_type: str,
        model_name: str,
        score: float,
        label: str,
        rationale: str,
        details: dict | None,
    ) -> AIPrediction:
        row = AIPrediction(
            lead_id=lead_id,
            customer_id=customer_id,
            prediction_type=prediction_type,
            model_name=model_name,
            score=score,
            label=label,
            rationale=rationale,
            details=details,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_predictions_for_lead(self, db: Session, lead_id: int, limit: int = 100) -> list[AIPrediction]:
        stmt = (
            select(AIPrediction)
            .where(AIPrediction.lead_id == lead_id)
            .order_by(AIPrediction.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def list_predictions_for_customer(self, db: Session, customer_id: int, limit: int = 100) -> list[AIPrediction]:
        stmt = (
            select(AIPrediction)
            .where(AIPrediction.customer_id == customer_id)
            .order_by(AIPrediction.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_lead(self, db: Session, lead_id: int) -> Lead | None:
        return db.get(Lead, lead_id)

    def get_customer(self, db: Session, customer_id: int) -> Customer | None:
        return db.get(Customer, customer_id)

    def lead_call_count(self, db: Session, lead_id: int) -> int:
        stmt = select(func.count(Call.id)).where(Call.lead_id == lead_id)
        return int(db.scalar(stmt) or 0)

    def lead_engagement_count(self, db: Session, lead_id: int) -> int:
        stmt = select(func.count(EngagementEvent.id)).where(EngagementEvent.lead_id == lead_id)
        return int(db.scalar(stmt) or 0)
