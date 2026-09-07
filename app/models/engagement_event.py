from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EngagementEvent(Base):
    __tablename__ = "engagement_events"
    __table_args__ = (
        Index("ix_engagement_events_lead_channel_event_time", "lead_id", "channel", "event_time"),
        Index("ix_engagement_events_campaign_channel_event_time", "campaign_id", "channel", "event_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metric_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    event_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    excel_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
