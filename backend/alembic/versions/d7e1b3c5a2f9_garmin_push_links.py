"""garmin_push_links: what was sent to each athlete's Garmin calendar, and the day's send count."""

from sqlalchemy import text

from alembic import op

revision = "d7e1b3c5a2f9"
down_revision = "c4d8e2f1a9b7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS garmin_push_links (
            user_id         INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            plan_id         INTEGER REFERENCES plans(id) ON DELETE SET NULL,
            day_hashes      JSONB NOT NULL DEFAULT '{}'::jsonb,
            scheduled       JSONB NOT NULL DEFAULT '{}'::jsonb,
            last_pushed_at  TIMESTAMPTZ,
            last_summary    JSONB,
            partial         BOOLEAN NOT NULL DEFAULT FALSE,
            usage_date      DATE,
            pushes          INTEGER NOT NULL DEFAULT 0
        )
        """)
    )


def downgrade():
    op.drop_table("garmin_push_links")
