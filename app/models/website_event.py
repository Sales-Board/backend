from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebsiteEvent(Base):
    __tablename__ = "website_events"
    __table_args__ = (
        Index("ix_website_events_lead_event_time", "lead_id", "event_time"),
        Index("ix_website_events_customer_event_time", "customer_id", "event_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    step_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    step_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_repeat_visitor: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    event_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    excel_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
