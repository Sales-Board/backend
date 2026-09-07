"""remove customer and product fields absent from Excel

Revision ID: 20260908_0019
Revises: 20260908_0018
Create Date: 2026-09-08 04:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260908_0019"
down_revision: str | Sequence[str] | None = "20260908_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("customers", "email")
    op.drop_column("customers", "phone")
    op.drop_column("products", "category")
    op.drop_column("products", "is_active")


def downgrade() -> None:
    import sqlalchemy as sa

    op.add_column("products", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("products", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("customers", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("customers", sa.Column("email", sa.String(length=255), nullable=True))
