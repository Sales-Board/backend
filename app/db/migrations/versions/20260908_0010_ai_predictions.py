"""create ai predictions table

Revision ID: 20260908_0010
Revises: 20260908_0009
Create Date: 2026-09-08 01:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0010"
down_revision: str | Sequence[str] | None = "20260908_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_predictions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("prediction_type", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ai_predictions_id", "ai_predictions", ["id"], unique=False)
    op.create_index("ix_ai_predictions_lead_id", "ai_predictions", ["lead_id"], unique=False)
    op.create_index("ix_ai_predictions_customer_id", "ai_predictions", ["customer_id"], unique=False)
    op.create_index("ix_ai_predictions_prediction_type", "ai_predictions", ["prediction_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_predictions_prediction_type", table_name="ai_predictions")
    op.drop_index("ix_ai_predictions_customer_id", table_name="ai_predictions")
    op.drop_index("ix_ai_predictions_lead_id", table_name="ai_predictions")
    op.drop_index("ix_ai_predictions_id", table_name="ai_predictions")
    op.drop_table("ai_predictions")
