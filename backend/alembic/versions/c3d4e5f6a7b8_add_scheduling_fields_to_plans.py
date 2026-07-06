"""add scheduling fields to plans

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-07-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("preferred_run_days", sa.Text(), nullable=True))
    op.add_column("plans", sa.Column("long_run_day", sa.Text(), nullable=True))
    op.add_column("plans", sa.Column("days_per_week", sa.Integer(), nullable=True, server_default="4"))
    op.add_column("plans", sa.Column("double_session_days", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "double_session_days")
    op.drop_column("plans", "days_per_week")
    op.drop_column("plans", "long_run_day")
    op.drop_column("plans", "preferred_run_days")
