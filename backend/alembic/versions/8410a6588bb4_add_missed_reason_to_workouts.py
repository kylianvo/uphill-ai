"""add missed_reason to workouts

Revision ID: 8410a6588bb4
Revises: b8e5f9c3a721
Create Date: 2026-10-20

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8410a6588bb4"
down_revision: str | Sequence[str] | None = "b8e5f9c3a721"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("missed_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "missed_reason")
