"""add plan_races (B-races) and workouts.plan_race_id

Revision ID: d1b7a3c9e2f4
Revises: c5a1d8e3f702
Create Date: 2026-10-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1b7a3c9e2f4"
down_revision: str | Sequence[str] | None = "c5a1d8e3f702"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plan_races",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("race_name", sa.Text(), nullable=False),
        sa.Column("course_ref", sa.Text(), nullable=True),
        sa.Column("race_date", sa.Date(), nullable=False),
        sa.Column("distance_km", sa.REAL(), nullable=False),
        sa.Column("elevation_gain_m", sa.REAL(), nullable=True),
        sa.Column("options_km", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("effort", sa.Text(), nullable=False, server_default="race"),
        sa.Column("status", sa.Text(), nullable=False, server_default="planned"),
        sa.Column("kept_against", sa.Text(), nullable=True),
        sa.Column("verdict", postgresql.JSONB(), nullable=True),
        sa.Column("verdict_text", postgresql.JSONB(), nullable=True),
        sa.Column("predicted", postgresql.JSONB(), nullable=True),
        sa.Column("result_seconds", sa.Integer(), nullable=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("debrief", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("idx_plan_races_plan_status", "plan_races", ["plan_id", "status"])
    op.add_column(
        "workouts",
        sa.Column("plan_race_id", sa.Integer(), sa.ForeignKey("plan_races.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workouts", "plan_race_id")
    op.drop_index("idx_plan_races_plan_status", table_name="plan_races")
    op.drop_table("plan_races")
