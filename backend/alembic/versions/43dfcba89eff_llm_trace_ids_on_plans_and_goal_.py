"""llm trace ids on plans and goal assessments

Revision ID: 43dfcba89eff
Revises: 111bf7f84a83
Create Date: 2026-09-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "43dfcba89eff"
down_revision: str | Sequence[str] | None = "111bf7f84a83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Langfuse trace ids that later outcome scores attach to (block compliance, plan
    # rework, race outcome). Metadata only: the traces carry no prompts or replies.
    op.add_column("plans", sa.Column("generation_trace_id", sa.Text(), nullable=True))
    op.add_column("plans", sa.Column("generation_block", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("generation_traced_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("goal_assessments", sa.Column("trace_id", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("goal_assessments", "trace_id")
    op.drop_column("plans", "generation_traced_at")
    op.drop_column("plans", "generation_block")
    op.drop_column("plans", "generation_trace_id")
