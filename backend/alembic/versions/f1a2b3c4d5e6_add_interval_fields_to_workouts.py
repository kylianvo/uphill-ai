"""add_interval_fields_to_workouts

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-07-17 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("interval_reps", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("interval_rep_value", sa.REAL(), nullable=True))
    op.add_column("workouts", sa.Column("interval_rep_unit", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "interval_rep_unit")
    op.drop_column("workouts", "interval_rep_value")
    op.drop_column("workouts", "interval_reps")
