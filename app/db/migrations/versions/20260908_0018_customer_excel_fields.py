"""store source Excel fields on customers

Revision ID: 20260908_0018
Revises: 20260908_0017
Create Date: 2026-09-08 03:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260908_0018"
down_revision: str | Sequence[str] | None = "20260908_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("excel_fields", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "excel_fields")
