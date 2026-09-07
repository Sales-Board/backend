"""create tasks and followups tables

Revision ID: 20260908_0012
Revises: 20260908_0011
Create Date: 2026-09-08 02:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0012"
down_revision: str | Sequence[str] | None = "20260908_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=False)
    op.create_index("ix_tasks_lead_id", "tasks", ["lead_id"], unique=False)
    op.create_index("ix_tasks_customer_id", "tasks", ["customer_id"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)

    op.create_table(
        "followups",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="call"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_followups_id", "followups", ["id"], unique=False)
    op.create_index("ix_followups_task_id", "followups", ["task_id"], unique=False)
    op.create_index("ix_followups_lead_id", "followups", ["lead_id"], unique=False)
    op.create_index("ix_followups_customer_id", "followups", ["customer_id"], unique=False)
    op.create_index("ix_followups_status", "followups", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_followups_status", table_name="followups")
    op.drop_index("ix_followups_customer_id", table_name="followups")
    op.drop_index("ix_followups_lead_id", table_name="followups")
    op.drop_index("ix_followups_task_id", table_name="followups")
    op.drop_index("ix_followups_id", table_name="followups")
    op.drop_table("followups")

    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_customer_id", table_name="tasks")
    op.drop_index("ix_tasks_lead_id", table_name="tasks")
    op.drop_index("ix_tasks_id", table_name="tasks")
    op.drop_table("tasks")
