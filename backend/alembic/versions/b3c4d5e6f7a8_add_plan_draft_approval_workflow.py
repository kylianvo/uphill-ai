"""add_plan_draft_approval_workflow

Revision ID: b3c4d5e6f7a8
Revises: a7b8c9d0e1f2
Create Date: 2026-07-24 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str | Sequence[str] | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("plans", sa.Column("plan_status", sa.Text(), nullable=False, server_default="active"))
    op.add_column("plans", sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("plans", sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.execute("UPDATE plans SET created_by_user_id = user_id WHERE created_by_user_id IS NULL")
    op.add_column("workouts", sa.Column("source", sa.Text(), nullable=False, server_default="ai_generated"))
    op.add_column(
        "workouts", sa.Column("last_edited_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("workouts", "last_edited_by_user_id")
    op.drop_column("workouts", "source")
    op.drop_column("plans", "approved_at")
    op.drop_column("plans", "approved_by_user_id")
    op.drop_column("plans", "plan_status")
    op.drop_column("plans", "created_by_user_id")
