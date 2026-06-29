"""create initial schema

Revision ID: bde4e6f04976
Revises:
Create Date: 2026-06-17 01:30:55.800873

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bde4e6f04976"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id                      SERIAL PRIMARY KEY,
        email                   TEXT UNIQUE NOT NULL,
        name                    TEXT,
        role                    TEXT NOT NULL DEFAULT 'user',
        provider                TEXT NOT NULL DEFAULT 'email',
        provider_user_id        TEXT,
        password_hash           TEXT,
        dob                     DATE,
        age                     INTEGER DEFAULT 30,
        current_weekly_km       REAL DEFAULT 30.0,
        max_hr                  INTEGER DEFAULT 185,
        resting_hr              INTEGER DEFAULT 60,
        aet_hr                  INTEGER DEFAULT 135,
        ant_hr                  INTEGER DEFAULT 165,
        zone2_pace_min          TEXT DEFAULT '6:30',
        zone2_pace_max          TEXT DEFAULT '5:45',
        onboarding_complete     BOOLEAN DEFAULT FALSE,
        goal_type               TEXT,
        injury_history          TEXT,
        preferred_run_days      TEXT,
        long_run_day            TEXT,
        days_per_week           INTEGER DEFAULT 4,
        has_gym_access          BOOLEAN DEFAULT FALSE,
        use_treadmill           INTEGER DEFAULT 0,
        gemini_api_key          TEXT,
        created_at              TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_token   TEXT PRIMARY KEY,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at      TIMESTAMPTZ NOT NULL
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id          SERIAL PRIMARY KEY,
        title       TEXT NOT NULL,
        type        TEXT NOT NULL,
        content     TEXT NOT NULL,
        url_path    TEXT,
        summary     TEXT,
        created_at  TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id                      SERIAL PRIMARY KEY,
        user_id                 INTEGER REFERENCES users(id) ON DELETE CASCADE,
        race_name               TEXT NOT NULL,
        race_date               TEXT NOT NULL,
        goal_type               TEXT NOT NULL,
        target_time_hours       REAL,
        total_weeks             INTEGER NOT NULL,
        current_week            INTEGER DEFAULT 1,
        course_distance_km      REAL,
        course_elevation_gain_m REAL,
        created_at              TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id                  SERIAL PRIMARY KEY,
        plan_id             INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
        week_number         INTEGER NOT NULL,
        day_of_week         TEXT NOT NULL,
        phase               TEXT NOT NULL,
        title               TEXT NOT NULL,
        type                TEXT NOT NULL,
        duration_minutes    REAL NOT NULL,
        distance_km         REAL,
        target_zone         TEXT NOT NULL,
        target_hr_range     TEXT,
        target_pace         TEXT,
        treadmill_incline   REAL DEFAULT 0.0,
        treadmill_speed     REAL DEFAULT 0.0,
        description         TEXT,
        fueling_tip         TEXT,
        is_completed        INTEGER DEFAULT 0
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS nutrition_products (
        id              SERIAL PRIMARY KEY,
        brand           TEXT NOT NULL,
        name            TEXT NOT NULL,
        type            TEXT NOT NULL,
        carbs_grams     REAL NOT NULL,
        sodium_mg       REAL NOT NULL,
        caffeine_mg     REAL DEFAULT 0.0,
        water_ratio_ml  REAL DEFAULT 250.0
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS shoes (
        id              SERIAL PRIMARY KEY,
        brand           TEXT NOT NULL,
        model           TEXT NOT NULL,
        surface         TEXT NOT NULL,
        cushioning      TEXT NOT NULL,
        drop_mm         INTEGER DEFAULT 6,
        plate           TEXT DEFAULT 'none',
        width           TEXT DEFAULT 'normal',
        review_summary  TEXT
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_cards (
        id              SERIAL PRIMARY KEY,
        chapter_title   TEXT NOT NULL,
        summary         TEXT NOT NULL,
        key_points      TEXT NOT NULL,
        tags            TEXT NOT NULL,
        topic           TEXT NOT NULL,
        source_label    TEXT DEFAULT 'Uphill Athlete Podcasts',
        created_at      TIMESTAMPTZ DEFAULT NOW()
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_cards CASCADE")
    op.execute("DROP TABLE IF EXISTS shoes CASCADE")
    op.execute("DROP TABLE IF EXISTS nutrition_products CASCADE")
    op.execute("DROP TABLE IF EXISTS workouts CASCADE")
    op.execute("DROP TABLE IF EXISTS plans CASCADE")
    op.execute("DROP TABLE IF EXISTS sources CASCADE")
    op.execute("DROP TABLE IF EXISTS sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
