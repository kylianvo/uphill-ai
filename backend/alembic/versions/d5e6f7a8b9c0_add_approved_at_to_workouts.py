"""add_approved_at_to_workouts

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-26 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True))
    # Backfill: workouts on already-active plans predate per-workout approval
    # and are implicitly approved; only draft-plan workouts stay pending.
    op.execute(
        "UPDATE workouts SET approved_at = NOW() WHERE approved_at IS NULL "
        "AND plan_id IN (SELECT id FROM plans WHERE plan_status = 'active')"
    )


def downgrade() -> None:
    op.drop_column("workouts", "approved_at")
