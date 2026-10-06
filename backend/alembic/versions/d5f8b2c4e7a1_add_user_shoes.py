"""Add user_shoes (the native app's Shoe Rotation).

Revision ID: d5f8b2c4e7a1
Revises: c3e7a9d1f5b2
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d5f8b2c4e7a1"
down_revision: str | Sequence[str] | None = "c3e7a9d1f5b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_shoes (
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            slot            TEXT NOT NULL,
            brand           TEXT NOT NULL,
            model           TEXT NOT NULL,
            distance_km     REAL NOT NULL DEFAULT 0,
            max_distance_km REAL NOT NULL DEFAULT 700,
            is_retired      BOOLEAN NOT NULL DEFAULT FALSE,
            notes           TEXT,
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, slot)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_shoes")
