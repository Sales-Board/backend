"""add crm-specific customer fields

Revision ID: 20260908_0015
Revises: 20260908_0014
Create Date: 2026-09-08 03:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0015"
down_revision: str | Sequence[str] | None = "20260908_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("crm_gender", sa.String(length=32), nullable=True))
    op.add_column("customers", sa.Column("crm_age_band", sa.String(length=32), nullable=True))
    op.add_column("customers", sa.Column("crm_income_band", sa.String(length=32), nullable=True))
    op.add_column("customers", sa.Column("crm_occupation", sa.String(length=100), nullable=True))
    op.add_column("customers", sa.Column("crm_education", sa.String(length=100), nullable=True))
    op.add_column("customers", sa.Column("crm_tobacco_user", sa.String(length=16), nullable=True))
    op.add_column("customers", sa.Column("crm_nonresident_flag", sa.String(length=16), nullable=True))
    op.add_column("customers", sa.Column("crm_existing_plan_flag", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "crm_existing_plan_flag")
    op.drop_column("customers", "crm_nonresident_flag")
    op.drop_column("customers", "crm_tobacco_user")
    op.drop_column("customers", "crm_education")
    op.drop_column("customers", "crm_occupation")
    op.drop_column("customers", "crm_income_band")
    op.drop_column("customers", "crm_age_band")
    op.drop_column("customers", "crm_gender")
