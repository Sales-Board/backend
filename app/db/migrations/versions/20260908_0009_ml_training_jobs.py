"""create ml training jobs table

Revision ID: 20260908_0009
Revises: 20260908_0008
Create Date: 2026-09-08 00:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0009"
down_revision: str | Sequence[str] | None = "20260908_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ml_training_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("training_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ml_training_jobs_id", "ml_training_jobs", ["id"], unique=False)
    op.create_index("ix_ml_training_jobs_model_name", "ml_training_jobs", ["model_name"], unique=False)
    op.create_index("ix_ml_training_jobs_status", "ml_training_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ml_training_jobs_status", table_name="ml_training_jobs")
    op.drop_index("ix_ml_training_jobs_model_name", table_name="ml_training_jobs")
    op.drop_index("ix_ml_training_jobs_id", table_name="ml_training_jobs")
    op.drop_table("ml_training_jobs")
