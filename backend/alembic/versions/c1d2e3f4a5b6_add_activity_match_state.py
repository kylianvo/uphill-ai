"""add activity match state

Revision ID: c1d2e3f4a5b6
Revises: 3906580d46f5
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "3906580d46f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("matched_workout_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_activities_matched_workout",
        "activities",
        "workouts",
        ["matched_workout_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("activities", sa.Column("match_confidence", sa.REAL(), nullable=True))
    op.add_column("activities", sa.Column("match_method", sa.Text(), nullable=True))
    op.add_column("activities", sa.Column("match_details", postgresql.JSONB(), nullable=True))
    op.create_index(
        "idx_activities_matched_workout",
        "activities",
        ["matched_workout_id"],
        unique=True,
        postgresql_where=sa.text("matched_workout_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_activities_matched_workout", table_name="activities")
    op.drop_column("activities", "match_details")
    op.drop_column("activities", "match_method")
    op.drop_column("activities", "match_confidence")
    op.drop_constraint("fk_activities_matched_workout", "activities", type_="foreignkey")
    op.drop_column("activities", "matched_workout_id")
