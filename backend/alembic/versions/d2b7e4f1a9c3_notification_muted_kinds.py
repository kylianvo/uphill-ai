"""Per-kind notification mutes ("Less like this")."""

from alembic import op

revision = "d2b7e4f1a9c3"
down_revision = "a6f2c8d9e104"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS muted_kinds TEXT[] NOT NULL DEFAULT '{}'")


def downgrade():
    op.drop_column("notification_preferences", "muted_kinds")
