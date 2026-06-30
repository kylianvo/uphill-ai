"""add sequential plan schema: session_slot, double_session_days, block_reviews

Revision ID: a1b2c3d4e5f6
Revises: bde4e6f04976
Create Date: 2026-06-30

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "bde4e6f04976"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE workouts ADD COLUMN IF NOT EXISTS rpe INTEGER")
    op.execute("ALTER TABLE workouts ADD COLUMN IF NOT EXISTS notes TEXT")
    op.execute("ALTER TABLE workouts ADD COLUMN IF NOT EXISTS session_slot TEXT DEFAULT 'main'")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS double_session_days TEXT")
    op.execute("""
    CREATE TABLE IF NOT EXISTS block_reviews (
        id           SERIAL PRIMARY KEY,
        plan_id      INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
        block_number INTEGER NOT NULL,
        overall_rpe  INTEGER,
        notes        TEXT,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS block_reviews CASCADE")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS double_session_days")
    op.execute("ALTER TABLE workouts DROP COLUMN IF EXISTS session_slot")
    op.execute("ALTER TABLE workouts DROP COLUMN IF EXISTS notes")
    op.execute("ALTER TABLE workouts DROP COLUMN IF EXISTS rpe")
