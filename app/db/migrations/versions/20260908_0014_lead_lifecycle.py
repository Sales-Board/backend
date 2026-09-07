"""add lead lifecycle tables and state fields

Revision ID: 20260908_0014
Revises: 20260908_0013
Create Date: 2026-09-08 08:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260908_0014"
down_revision: str | Sequence[str] | None = "20260908_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("current_stage", sa.String(length=32), nullable=False, server_default="generated"))
    op.add_column("leads", sa.Column("current_section", sa.String(length=64), nullable=True, server_default="intake"))
    op.add_column("leads", sa.Column("current_handler", sa.String(length=100), nullable=True))
    op.add_column("leads", sa.Column("lead_score", sa.Float(), nullable=True))
    op.add_column("leads", sa.Column("recommended_action", sa.String(length=64), nullable=True))

    op.create_table(
        "lead_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("assignment_type", sa.String(length=32), nullable=False, server_default="assign"),
        sa.Column("from_section", sa.String(length=64), nullable=True),
        sa.Column("to_section", sa.String(length=64), nullable=True),
        sa.Column("from_handler", sa.String(length=100), nullable=True),
        sa.Column("to_handler", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("trigger", sa.String(length=64), nullable=True),
        sa.Column("related_decision_id", sa.Integer(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_decision_id"], ["decision_recommendations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_lead_assignments_id", "lead_assignments", ["id"], unique=False)
    op.create_index("ix_lead_assignments_lead_id", "lead_assignments", ["lead_id"], unique=False)
    op.create_index("ix_lead_assignments_customer_id", "lead_assignments", ["customer_id"], unique=False)
    op.create_index("ix_lead_assignments_related_decision_id", "lead_assignments", ["related_decision_id"], unique=False)
    op.create_index("ix_lead_assignments_is_current", "lead_assignments", ["is_current"], unique=False)

    op.create_table(
        "lead_timeline_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_source", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_lead_timeline_events_id", "lead_timeline_events", ["id"], unique=False)
    op.create_index("ix_lead_timeline_events_lead_id", "lead_timeline_events", ["lead_id"], unique=False)
    op.create_index("ix_lead_timeline_events_customer_id", "lead_timeline_events", ["customer_id"], unique=False)
    op.create_index("ix_lead_timeline_events_event_type", "lead_timeline_events", ["event_type"], unique=False)
    op.create_index("ix_lead_timeline_events_created_at", "lead_timeline_events", ["created_at"], unique=False)

    op.create_table(
        "lead_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("outcome_code", sa.String(length=64), nullable=False),
        sa.Column("outcome_label", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("followup_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("next_action_hint", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_lead_outcomes_id", "lead_outcomes", ["id"], unique=False)
    op.create_index("ix_lead_outcomes_lead_id", "lead_outcomes", ["lead_id"], unique=False)
    op.create_index("ix_lead_outcomes_customer_id", "lead_outcomes", ["customer_id"], unique=False)
    op.create_index("ix_lead_outcomes_outcome_code", "lead_outcomes", ["outcome_code"], unique=False)
    op.create_index("ix_lead_outcomes_created_at", "lead_outcomes", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_outcomes_created_at", table_name="lead_outcomes")
    op.drop_index("ix_lead_outcomes_outcome_code", table_name="lead_outcomes")
    op.drop_index("ix_lead_outcomes_customer_id", table_name="lead_outcomes")
    op.drop_index("ix_lead_outcomes_lead_id", table_name="lead_outcomes")
    op.drop_index("ix_lead_outcomes_id", table_name="lead_outcomes")
    op.drop_table("lead_outcomes")

    op.drop_index("ix_lead_timeline_events_created_at", table_name="lead_timeline_events")
    op.drop_index("ix_lead_timeline_events_event_type", table_name="lead_timeline_events")
    op.drop_index("ix_lead_timeline_events_customer_id", table_name="lead_timeline_events")
    op.drop_index("ix_lead_timeline_events_lead_id", table_name="lead_timeline_events")
    op.drop_index("ix_lead_timeline_events_id", table_name="lead_timeline_events")
    op.drop_table("lead_timeline_events")

    op.drop_index("ix_lead_assignments_is_current", table_name="lead_assignments")
    op.drop_index("ix_lead_assignments_related_decision_id", table_name="lead_assignments")
    op.drop_index("ix_lead_assignments_customer_id", table_name="lead_assignments")
    op.drop_index("ix_lead_assignments_lead_id", table_name="lead_assignments")
    op.drop_index("ix_lead_assignments_id", table_name="lead_assignments")
    op.drop_table("lead_assignments")

    op.drop_column("leads", "recommended_action")
    op.drop_column("leads", "lead_score")
    op.drop_column("leads", "current_handler")
    op.drop_column("leads", "current_section")
    op.drop_column("leads", "current_stage")
