"""create campaigns and engagement events

Revision ID: 20260907_0005
Revises: 20260907_0004
Create Date: 2026-09-07 01:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260907_0005"
down_revision: str | Sequence[str] | None = "20260907_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("channel", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_campaigns_code", "campaigns", ["code"], unique=True)
    op.create_index("ix_campaigns_id", "campaigns", ["id"], unique=False)

    op.add_column("leads", sa.Column("campaign_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_leads_campaign_id_campaigns",
        "leads",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_leads_campaign_id", "leads", ["campaign_id"], unique=False)

    op.create_table(
        "engagement_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("metric_type", sa.String(length=32), nullable=False),
        sa.Column("metric_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_payload", sa.JSON(), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_engagement_events_id", "engagement_events", ["id"], unique=False)
    op.create_index("ix_engagement_events_lead_id", "engagement_events", ["lead_id"], unique=False)
    op.create_index("ix_engagement_events_customer_id", "engagement_events", ["customer_id"], unique=False)
    op.create_index("ix_engagement_events_campaign_id", "engagement_events", ["campaign_id"], unique=False)
    op.create_index("ix_engagement_events_channel", "engagement_events", ["channel"], unique=False)
    op.create_index("ix_engagement_events_metric_type", "engagement_events", ["metric_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_engagement_events_metric_type", table_name="engagement_events")
    op.drop_index("ix_engagement_events_channel", table_name="engagement_events")
    op.drop_index("ix_engagement_events_campaign_id", table_name="engagement_events")
    op.drop_index("ix_engagement_events_customer_id", table_name="engagement_events")
    op.drop_index("ix_engagement_events_lead_id", table_name="engagement_events")
    op.drop_index("ix_engagement_events_id", table_name="engagement_events")
    op.drop_table("engagement_events")

    op.drop_index("ix_leads_campaign_id", table_name="leads")
    op.drop_constraint("fk_leads_campaign_id_campaigns", "leads", type_="foreignkey")
    op.drop_column("leads", "campaign_id")

    op.drop_index("ix_campaigns_id", table_name="campaigns")
    op.drop_index("ix_campaigns_code", table_name="campaigns")
    op.drop_table("campaigns")
