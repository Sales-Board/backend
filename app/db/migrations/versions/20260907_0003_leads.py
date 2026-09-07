"""create leads table

Revision ID: 20260907_0003
Revises: 20260907_0002
Create Date: 2026-09-07 00:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260907_0003"
down_revision: str | Sequence[str] | None = "20260907_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("source_channel", sa.String(length=64), nullable=True),
        sa.Column("source_medium", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_leads_id", "leads", ["id"], unique=False)
    op.create_index("ix_leads_customer_id", "leads", ["customer_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_leads_customer_id", table_name="leads")
    op.drop_index("ix_leads_id", table_name="leads")
    op.drop_table("leads")
