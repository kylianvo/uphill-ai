"""coach plan type per athlete and per-week plan review columns

Revision ID: b3c7e9a1d2f4
Revises: a9d4c7e1f2b6
Create Date: 2026-10-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c7e9a1d2f4"
down_revision: str | Sequence[str] | None = "a9d4c7e1f2b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("coach_athletes", sa.Column("plan_type", sa.Text(), nullable=False, server_default="review"))
    op.add_column("plans", sa.Column("coach_reviewed_block", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("coach_reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("plans", sa.Column("coach_reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "coach_reviewed_by")
    op.drop_column("plans", "coach_reviewed_at")
    op.drop_column("plans", "coach_reviewed_block")
    op.drop_column("coach_athletes", "plan_type")
