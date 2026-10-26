"""The coach's weekly review on coach_nudges: three messages and the session to nail."""

from alembic import op

revision = "c4e8b2a7d915"
down_revision = "d2b7e4f1a9c3"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE coach_nudges ADD COLUMN IF NOT EXISTS messages JSONB")
    op.execute("ALTER TABLE coach_nudges ADD COLUMN IF NOT EXISTS nail TEXT")


def downgrade():
    op.drop_column("coach_nudges", "nail")
    op.drop_column("coach_nudges", "messages")
