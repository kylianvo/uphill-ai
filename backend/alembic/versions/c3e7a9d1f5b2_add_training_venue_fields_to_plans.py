"""add training venue fields to plans (mountain days, stair access, treadmill max incline)

Revision ID: c3e7a9d1f5b2
Revises: b8d2f4a6c1e3
Create Date: 2026-10-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3e7a9d1f5b2"
down_revision: str | Sequence[str] | None = "b8d2f4a6c1e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("mountain_days", sa.Text(), nullable=True))
    op.add_column("plans", sa.Column("stair_access", sa.Boolean(), server_default=sa.false(), nullable=True))
    op.add_column("plans", sa.Column("treadmill_max_incline", sa.Integer(), server_default="15", nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "treadmill_max_incline")
    op.drop_column("plans", "stair_access")
    op.drop_column("plans", "mountain_days")
