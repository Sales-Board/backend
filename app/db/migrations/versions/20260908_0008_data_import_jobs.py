"""create data import jobs table

Revision ID: 20260908_0008
Revises: 20260907_0007
Create Date: 2026-09-08 00:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0008"
down_revision: str | Sequence[str] | None = "20260907_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dataset_name", sa.String(length=100), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_data_import_jobs_id", "data_import_jobs", ["id"], unique=False)
    op.create_index("ix_data_import_jobs_dataset_name", "data_import_jobs", ["dataset_name"], unique=False)
    op.create_index("ix_data_import_jobs_status", "data_import_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_data_import_jobs_status", table_name="data_import_jobs")
    op.drop_index("ix_data_import_jobs_dataset_name", table_name="data_import_jobs")
    op.drop_index("ix_data_import_jobs_id", table_name="data_import_jobs")
    op.drop_table("data_import_jobs")
