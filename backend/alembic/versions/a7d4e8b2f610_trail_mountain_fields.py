"""Training mountain preferences and per-workout mountain mode.

Revision ID: a7d4e8b2f610
Revises: c8e2a4f6d9b1
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7d4e8b2f610"
down_revision: str | Sequence[str] | None = "c8e2a4f6d9b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("training_mountain", sa.Text(), nullable=True))
    op.add_column("plans", sa.Column("mountain_min_minutes", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("mountain_mode", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "mountain_mode")
    op.drop_column("plans", "mountain_min_minutes")
    op.drop_column("plans", "training_mountain")
