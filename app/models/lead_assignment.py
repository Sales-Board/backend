from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LeadAssignment(Base):
    __tablename__ = "lead_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assignment_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="assign")
    from_section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    from_handler: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_handler: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trigger: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_decision_id: Mapped[int | None] = mapped_column(
        ForeignKey("decision_recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
