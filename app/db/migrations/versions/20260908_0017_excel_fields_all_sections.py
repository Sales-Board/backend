"""store source Excel fields on all domain sections

Revision ID: 20260908_0017
Revises: 20260908_0016
Create Date: 2026-09-08 03:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260908_0017"
down_revision: str | Sequence[str] | None = "20260908_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "products",
    "campaigns",
    "engagement_events",
    "website_events",
    "calls",
    "tasks",
    "followups",
    "lead_assignments",
    "lead_timeline_events",
    "lead_outcomes",
)


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("excel_fields", sa.JSON(), nullable=True))


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_column(table, "excel_fields")
