"""create website events

Revision ID: 20260907_0006
Revises: 20260907_0005
Create Date: 2026-09-07 02:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260907_0006"
down_revision: str | Sequence[str] | None = "20260907_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "website_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("step_name", sa.String(length=100), nullable=True),
        sa.Column("step_number", sa.Integer(), nullable=True),
        sa.Column("device_type", sa.String(length=32), nullable=True),
        sa.Column("is_repeat_visitor", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("event_payload", sa.JSON(), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_website_events_id", "website_events", ["id"], unique=False)
    op.create_index("ix_website_events_lead_id", "website_events", ["lead_id"], unique=False)
    op.create_index("ix_website_events_customer_id", "website_events", ["customer_id"], unique=False)
    op.create_index("ix_website_events_event_name", "website_events", ["event_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_website_events_event_name", table_name="website_events")
    op.drop_index("ix_website_events_customer_id", table_name="website_events")
    op.drop_index("ix_website_events_lead_id", table_name="website_events")
    op.drop_index("ix_website_events_id", table_name="website_events")
    op.drop_table("website_events")
