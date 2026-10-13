"""Add optional location to race results."""

from alembic import op

revision = "a713c9e6f024"
down_revision = "d5f8b2c4e7a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE race_results ADD COLUMN IF NOT EXISTS location TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE race_results DROP COLUMN IF EXISTS location")
