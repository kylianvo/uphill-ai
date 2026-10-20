"""Preserve the original mountain climb rate across mode switches.

Revision ID: b8e5f9c3a721
Revises: a7d4e8b2f610
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8e5f9c3a721"
down_revision: str | Sequence[str] | None = "a7d4e8b2f610"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("mountain_climb_rate", sa.REAL(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "mountain_climb_rate")
