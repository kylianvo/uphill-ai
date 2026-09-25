"""Add race history, UTMB/VBM search mirrors, and plan scenarios.

Revision ID: e8a4c2f6b1d3
Revises: d3f7b9a1c5e2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e8a4c2f6b1d3"
down_revision: str | Sequence[str] | None = "d3f7b9a1c5e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("prediction", postgresql.JSONB(), nullable=True))
    op.execute("""
        CREATE TABLE race_profile_claims (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source TEXT NOT NULL CHECK (source IN ('utmb', 'vbm')),
            external_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            meta JSONB NOT NULL DEFAULT '{}'::jsonb,
            verified BOOLEAN NOT NULL DEFAULT FALSE,
            verification_methods TEXT[] NOT NULL DEFAULT '{}',
            sync_status TEXT NOT NULL DEFAULT 'pending',
            sync_error TEXT,
            sync_attempts INTEGER NOT NULL DEFAULT 0,
            sync_requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_synced_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, source, external_id),
            UNIQUE (id, user_id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_race_claim_utmb ON race_profile_claims (external_id) WHERE source = 'utmb'")
    op.execute("""
        CREATE TABLE race_results (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_id INTEGER,
            source TEXT NOT NULL CHECK (source IN ('utmb', 'vbm', 'manual')),
            source_key TEXT NOT NULL,
            discipline TEXT NOT NULL CHECK (discipline IN ('trail', 'road')),
            race_name TEXT NOT NULL,
            event_name TEXT,
            race_date DATE NOT NULL,
            country_code TEXT,
            distance_km REAL NOT NULL,
            elevation_gain_m REAL,
            utmb_category TEXT,
            finish_time_sec INTEGER,
            is_dnf BOOLEAN NOT NULL DEFAULT FALSE,
            rank_overall INTEGER,
            total_overall INTEGER,
            rank_gender INTEGER,
            total_gender INTEGER,
            rank_age_group INTEGER,
            total_age_group INTEGER,
            bib TEXT,
            result_url TEXT,
            source_race_uri TEXT,
            is_pr BOOLEAN NOT NULL DEFAULT FALSE,
            selected BOOLEAN NOT NULL DEFAULT TRUE,
            hidden BOOLEAN NOT NULL DEFAULT FALSE,
            user_note TEXT,
            verified BOOLEAN NOT NULL DEFAULT FALSE,
            verification_methods TEXT[] NOT NULL DEFAULT '{}',
            matched_activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
            raw JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (claim_id, user_id) REFERENCES race_profile_claims(id, user_id) ON DELETE CASCADE,
            UNIQUE (claim_id, source_key)
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_race_result_manual_key ON race_results (source_key) WHERE source = 'manual'")
    op.execute("CREATE INDEX idx_race_results_user_date ON race_results (user_id, race_date DESC)")
    op.execute("""
        CREATE TABLE vbm_athletes (
            vbm_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            name_norm TEXT NOT NULL,
            sex_band TEXT,
            events JSONB NOT NULL DEFAULT '{}'::jsonb,
            clubs JSONB NOT NULL DEFAULT '[]'::jsonb,
            refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_vbm_athletes_name ON vbm_athletes (name_norm)")
    # Search-only copy of UTMB's runner index for Vietnamese runners (identity
    # fields, no results); results are fetched per claimed profile.
    op.execute("""
        CREATE TABLE utmb_runners (
            uri TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            name_norm TEXT NOT NULL,
            sex TEXT,
            age_group TEXT,
            utmb_index INTEGER,
            refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.drop_table("utmb_runners")
    op.drop_table("vbm_athletes")
    op.drop_table("race_results")
    op.drop_table("race_profile_claims")
    op.drop_column("plans", "prediction")
