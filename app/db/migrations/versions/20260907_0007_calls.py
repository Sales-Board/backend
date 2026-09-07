"""create calls table

Revision ID: 20260907_0007
Revises: 20260907_0006
Create Date: 2026-09-07 02:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260907_0007"
down_revision: str | Sequence[str] | None = "20260907_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calls",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(length=16), nullable=False, server_default="outbound"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="scheduled"),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_calls_id", "calls", ["id"], unique=False)
    op.create_index("ix_calls_lead_id", "calls", ["lead_id"], unique=False)
    op.create_index("ix_calls_customer_id", "calls", ["customer_id"], unique=False)
    op.create_index("ix_calls_status", "calls", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_calls_customer_id", table_name="calls")
    op.drop_index("ix_calls_lead_id", table_name="calls")
    op.drop_index("ix_calls_id", table_name="calls")
    op.drop_table("calls")
