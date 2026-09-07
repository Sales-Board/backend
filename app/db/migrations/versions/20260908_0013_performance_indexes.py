"""add performance indexes

Revision ID: 20260908_0013
Revises: 20260908_0012
Create Date: 2026-09-08 03:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0013"
down_revision: str | Sequence[str] | None = "20260908_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_leads_status_priority_created_at", "leads", ["status", "priority", "created_at"], unique=False)
    op.create_index("ix_leads_campaign_status", "leads", ["campaign_id", "status"], unique=False)

    op.create_index(
        "ix_engagement_events_lead_channel_event_time",
        "engagement_events",
        ["lead_id", "channel", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_engagement_events_campaign_channel_event_time",
        "engagement_events",
        ["campaign_id", "channel", "event_time"],
        unique=False,
    )

    op.create_index("ix_website_events_lead_event_time", "website_events", ["lead_id", "event_time"], unique=False)
    op.create_index(
        "ix_website_events_customer_event_time",
        "website_events",
        ["customer_id", "event_time"],
        unique=False,
    )

    op.create_index("ix_calls_lead_status", "calls", ["lead_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_calls_lead_status", table_name="calls")
    op.drop_index("ix_website_events_customer_event_time", table_name="website_events")
    op.drop_index("ix_website_events_lead_event_time", table_name="website_events")
    op.drop_index("ix_engagement_events_campaign_channel_event_time", table_name="engagement_events")
    op.drop_index("ix_engagement_events_lead_channel_event_time", table_name="engagement_events")
    op.drop_index("ix_leads_campaign_status", table_name="leads")
    op.drop_index("ix_leads_status_priority_created_at", table_name="leads")
