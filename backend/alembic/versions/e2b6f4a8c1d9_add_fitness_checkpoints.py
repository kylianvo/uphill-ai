"""add fitness_checkpoints

Revision ID: e2b6f4a8c1d9
Revises: d7c3a91e5b24
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2b6f4a8c1d9"
down_revision: str | Sequence[str] | None = "d7c3a91e5b24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fitness_checkpoints",
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("pace_min_km", sa.REAL(), nullable=False),
        sa.Column("n_runs", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("plan_id", "week_number"),
    )


def downgrade() -> None:
    op.drop_table("fitness_checkpoints")
