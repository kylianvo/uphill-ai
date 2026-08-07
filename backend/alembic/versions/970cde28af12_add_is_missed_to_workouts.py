"""add_is_missed_to_workouts

Revision ID: 970cde28af12
Revises: d5e6f7a8b9c0
Create Date: 2026-08-07 17:43:04.833461

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "970cde28af12"
down_revision: str | Sequence[str] | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("is_missed", sa.Integer(), nullable=True, server_default="0"))


def downgrade() -> None:
    op.drop_column("workouts", "is_missed")
