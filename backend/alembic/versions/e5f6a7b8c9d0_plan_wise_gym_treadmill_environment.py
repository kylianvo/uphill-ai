"""plan-wise gym access, treadmill, and training environment

Revision ID: e5f6a7b8c9d0
Revises: fb9587e7799f
Create Date: 2026-07-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "fb9587e7799f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("has_gym_access", sa.Boolean(), server_default=sa.false(), nullable=True))
    op.add_column("plans", sa.Column("use_treadmill", sa.Boolean(), server_default=sa.false(), nullable=True))
    op.add_column("plans", sa.Column("training_environment", sa.Text(), server_default="flat", nullable=True))
    op.drop_column("users", "has_gym_access")
    op.drop_column("users", "use_treadmill")
    op.drop_column("users", "double_session_days")


def downgrade() -> None:
    op.add_column("users", sa.Column("double_session_days", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("use_treadmill", sa.Integer(), server_default="0", nullable=True))
    op.add_column("users", sa.Column("has_gym_access", sa.Boolean(), server_default=sa.false(), nullable=True))
    op.drop_column("plans", "training_environment")
    op.drop_column("plans", "use_treadmill")
    op.drop_column("plans", "has_gym_access")
