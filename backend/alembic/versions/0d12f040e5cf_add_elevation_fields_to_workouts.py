"""add_elevation_fields_to_workouts

Revision ID: 0d12f040e5cf
Revises: d4e5f6a7b8c9
Create Date: 2026-07-06 10:05:53.253609

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d12f040e5cf"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("elevation_gain_m", sa.REAL(), server_default="0.0"))
    op.add_column("workouts", sa.Column("grade_percent", sa.REAL(), server_default="0.0"))


def downgrade() -> None:
    op.drop_column("workouts", "grade_percent")
    op.drop_column("workouts", "elevation_gain_m")
