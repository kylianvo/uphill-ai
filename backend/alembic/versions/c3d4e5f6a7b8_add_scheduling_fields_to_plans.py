"""add scheduling fields to plans

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-07-01 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE plans ADD COLUMN IF NOT EXISTS preferred_run_days TEXT")
    op.execute("ALTER TABLE plans ADD COLUMN IF NOT EXISTS long_run_day TEXT")
    op.execute("ALTER TABLE plans ADD COLUMN IF NOT EXISTS days_per_week INTEGER DEFAULT 4")
    op.execute("ALTER TABLE plans ADD COLUMN IF NOT EXISTS double_session_days TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE plans DROP COLUMN IF EXISTS double_session_days")
    op.execute("ALTER TABLE plans DROP COLUMN IF EXISTS days_per_week")
    op.execute("ALTER TABLE plans DROP COLUMN IF EXISTS long_run_day")
    op.execute("ALTER TABLE plans DROP COLUMN IF EXISTS preferred_run_days")
