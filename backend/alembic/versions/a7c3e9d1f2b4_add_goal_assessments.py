"""Add goal_assessments for LLM goal estimation.

Revision ID: a7c3e9d1f2b4
Revises: e8a4c2f6b1d3
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a7c3e9d1f2b4"
down_revision: str | Sequence[str] | None = "e8a4c2f6b1d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE goal_assessments (
            id                SERIAL PRIMARY KEY,
            user_id           INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- NULL = signed-out estimate
            plan_id           INTEGER REFERENCES plans(id) ON DELETE CASCADE,
            race_name         TEXT,
            race_date         DATE,
            distance_km       REAL NOT NULL,
            elevation_gain_m  REAL NOT NULL DEFAULT 0,
            input_hash        TEXT NOT NULL,
            context_summary   JSONB NOT NULL DEFAULT '{}'::jsonb,
            anchors           JSONB NOT NULL DEFAULT '[]'::jsonb,
            output            JSONB,                           -- NULL = no estimate possible
            engine            TEXT NOT NULL,                   -- 'gemini' | 'gemini_retry' | 'rules' | 'none'
            confidence        TEXT,
            lang              TEXT NOT NULL DEFAULT 'en',
            trigger           TEXT NOT NULL,                   -- 'pre_plan' | 'manual' | 'weekly'
            plan_week         INTEGER,
            actual_finish_sec INTEGER,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_goal_assessments_plan ON goal_assessments (plan_id, created_at DESC)")
    op.execute("CREATE INDEX idx_goal_assessments_user ON goal_assessments (user_id, created_at DESC)")
    op.execute(
        "CREATE UNIQUE INDEX uq_goal_assessments_weekly ON goal_assessments (plan_id, plan_week) "
        "WHERE trigger = 'weekly'"
    )


def downgrade() -> None:
    op.drop_table("goal_assessments")
