"""create decision recommendations table

Revision ID: 20260908_0011
Revises: 20260908_0010
Create Date: 2026-09-08 01:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0011"
down_revision: str | Sequence[str] | None = "20260908_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "decision_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("decision_type", sa.String(length=50), nullable=False),
        sa.Column("recommended_action", sa.String(length=120), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_decision_recommendations_id", "decision_recommendations", ["id"], unique=False)
    op.create_index("ix_decision_recommendations_lead_id", "decision_recommendations", ["lead_id"], unique=False)
    op.create_index("ix_decision_recommendations_customer_id", "decision_recommendations", ["customer_id"], unique=False)
    op.create_index("ix_decision_recommendations_decision_type", "decision_recommendations", ["decision_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_decision_recommendations_decision_type", table_name="decision_recommendations")
    op.drop_index("ix_decision_recommendations_customer_id", table_name="decision_recommendations")
    op.drop_index("ix_decision_recommendations_lead_id", table_name="decision_recommendations")
    op.drop_index("ix_decision_recommendations_id", table_name="decision_recommendations")
    op.drop_table("decision_recommendations")
