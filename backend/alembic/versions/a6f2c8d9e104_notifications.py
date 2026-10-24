"""Durable native notifications, opt-out by default."""

from sqlalchemy import text

from alembic import op

revision = "a6f2c8d9e104"
down_revision = "b3c7e9a1d2f4"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        text(
            "\nCREATE TABLE IF NOT EXISTS notification_preferences (\n user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,\n workouts_enabled BOOLEAN NOT NULL DEFAULT false, coaching_enabled BOOLEAN NOT NULL DEFAULT false,\n results_enabled BOOLEAN NOT NULL DEFAULT false, workout_time TEXT NOT NULL DEFAULT '07:00',\n coaching_time TEXT NOT NULL DEFAULT '18:00', quiet_start TEXT NOT NULL DEFAULT '21:00',\n quiet_end TEXT NOT NULL DEFAULT '07:00', timezone TEXT, language TEXT NOT NULL DEFAULT 'en',\n distance_unit TEXT NOT NULL DEFAULT 'km', paused_until TIMESTAMPTZ, checklist_snoozed_until TIMESTAMPTZ,\n last_proactive_at TIMESTAMPTZ, last_proactive_date DATE, result_date DATE, result_count INTEGER NOT NULL DEFAULT 0,\n next_evaluation_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n);\nCREATE TABLE IF NOT EXISTS notification_installations (\n id UUID PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n token TEXT NOT NULL, environment TEXT NOT NULL CHECK (environment IN ('sandbox','production')),\n permission TEXT NOT NULL CHECK (permission IN ('authorized','provisional','denied','notDetermined')),\n last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), disabled_at TIMESTAMPTZ,\n registration_revision INTEGER NOT NULL DEFAULT 1, UNIQUE(token,environment)\n);\nCREATE TABLE IF NOT EXISTS notification_events (\n id UUID PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n event_key TEXT NOT NULL, kind TEXT NOT NULL, destination JSONB NOT NULL, source JSONB NOT NULL DEFAULT '{}',\n due_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL,\n status TEXT NOT NULL CHECK(status IN ('pending','sending','accepted','suppressed','expired','failed','unknown')),\n installation_id UUID REFERENCES notification_installations(id) ON DELETE SET NULL,\n registration_revision INTEGER, attempts INTEGER NOT NULL DEFAULT 0, claimed_at TIMESTAMPTZ,\n next_attempt_at TIMESTAMPTZ, accepted_at TIMESTAMPTZ, opened_at TIMESTAMPTZ,\n result_code TEXT, suppression_reason TEXT, UNIQUE(user_id,event_key)\n);\nCREATE INDEX IF NOT EXISTS notification_due ON notification_preferences(next_evaluation_at);\nCREATE INDEX IF NOT EXISTS notification_pending ON notification_events(status,next_attempt_at);\nCREATE INDEX IF NOT EXISTS notification_history ON notification_events(user_id,kind,claimed_at);\nCREATE TABLE IF NOT EXISTS notification_knowledge_opens (\n user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, card_id INTEGER NOT NULL,\n lang TEXT NOT NULL, opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(user_id,card_id,lang)\n);\nCREATE TABLE IF NOT EXISTS notification_generation_requests (\n id UUID PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,\n coverage INTEGER, status TEXT NOT NULL CHECK(status IN ('generating','done','error')),\n updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), result JSONB\n);\nALTER TABLE workouts ADD COLUMN IF NOT EXISTS missed_origin TEXT;\nALTER TABLE workouts ADD COLUMN IF NOT EXISTS first_completed_at TIMESTAMPTZ;\nALTER TABLE knowledge_cards ADD COLUMN IF NOT EXISTS notification_reviewed BOOLEAN NOT NULL DEFAULT false;\n"
        )
    )


def downgrade():
    for name in (
        "notification_events",
        "notification_installations",
        "notification_preferences",
        "notification_knowledge_opens",
        "notification_generation_requests",
    ):
        op.drop_table(name)
    op.drop_column("workouts", "missed_origin")
    op.drop_column("workouts", "first_completed_at")
    op.drop_column("knowledge_cards", "notification_reviewed")
