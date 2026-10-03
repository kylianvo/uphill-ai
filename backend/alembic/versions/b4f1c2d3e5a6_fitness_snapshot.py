"""fitness snapshot: fitness_assessments history, users.threshold_source, plans.fitness_snapshot

Revision ID: b4f1c2d3e5a6
Revises: 43dfcba89eff
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b4f1c2d3e5a6"
down_revision: str | Sequence[str] | None = "43dfcba89eff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fitness_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("vo2max", sa.REAL()),
        sa.Column("running_level", sa.REAL()),
        sa.Column("threshold_pace", sa.Text()),
        sa.Column("pred_5k_sec", sa.REAL()),
        sa.Column("pred_10k_sec", sa.REAL()),
        sa.Column("pred_hm_sec", sa.REAL()),
        sa.Column("pred_marathon_sec", sa.REAL()),
        sa.Column("measured_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_fitness_assessments_user", "fitness_assessments", ["user_id", sa.text("measured_at DESC")])
    op.add_column("plans", sa.Column("fitness_snapshot", postgresql.JSONB()))
    op.add_column("users", sa.Column("threshold_source", sa.Text(), nullable=False, server_default="unknown"))


def downgrade() -> None:
    op.drop_column("users", "threshold_source")
    op.drop_column("plans", "fitness_snapshot")
    op.drop_index("idx_fitness_assessments_user", table_name="fitness_assessments")
    op.drop_table("fitness_assessments")
