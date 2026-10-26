"""add beginner milestones

Revision ID: c5a1d8e3f702
Revises: c4e8b2a7d915, c4d8e2f1a9b7
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5a1d8e3f702"
down_revision: str | Sequence[str] | None = ("c4e8b2a7d915", "c4d8e2f1a9b7")  # also merges the two heads on main
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("milestone_target", sa.Text(), nullable=True))
    op.add_column("plans", sa.Column("has_target_event", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")))
    op.create_table(
        "plan_milestones",
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("milestone_key", sa.Text(), nullable=False),
        sa.Column("achieved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("plan_id", "milestone_key"),
    )


def downgrade() -> None:
    op.drop_table("plan_milestones")
    op.drop_column("plans", "has_target_event")
    op.drop_column("plans", "milestone_target")
