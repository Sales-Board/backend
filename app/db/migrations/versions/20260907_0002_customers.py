"""create customers table

Revision ID: 20260907_0002
Revises: 20260907_0001
Create Date: 2026-09-07 00:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260907_0002"
down_revision: str | Sequence[str] | None = "20260907_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("external_customer_id", sa.String(length=64), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_customers_external_customer_id", "customers", ["external_customer_id"], unique=True)
    op.create_index("ix_customers_id", "customers", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_customers_id", table_name="customers")
    op.drop_index("ix_customers_external_customer_id", table_name="customers")
    op.drop_table("customers")
