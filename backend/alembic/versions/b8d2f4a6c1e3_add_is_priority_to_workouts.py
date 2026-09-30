"""Add is_priority to workouts.

Revision ID: b8d2f4a6c1e3
Revises: a7c3e9d1f2b4
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b8d2f4a6c1e3"
down_revision: str | Sequence[str] | None = "a7c3e9d1f2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE workouts ADD COLUMN IF NOT EXISTS is_priority BOOLEAN NOT NULL DEFAULT FALSE")


def downgrade() -> None:
    op.execute("ALTER TABLE workouts DROP COLUMN IF EXISTS is_priority")
