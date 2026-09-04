"""add device integration tables

Revision ID: b1c2d3e4f5a6
Revises: a023ef42dde9
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a023ef42dde9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athlete_connections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Text, nullable=False),
        sa.Column("provider_user_id", sa.Text),
        sa.Column("access_token_enc", sa.Text),
        sa.Column("refresh_token_enc", sa.Text),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("scopes", sa.Text),
        sa.Column("status", sa.Text, nullable=False, server_default="active"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "provider", name="uq_athlete_connections_user_provider"),
    )
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_provider", sa.Text, nullable=False),
        sa.Column("external_ids", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("device_model", sa.Text),
        sa.Column("activity_type", sa.Text, nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.REAL, nullable=False),
        sa.Column("distance_km", sa.REAL),
        sa.Column("elevation_gain_m", sa.REAL),
        sa.Column("elevation_loss_m", sa.REAL),
        sa.Column("avg_hr", sa.Integer),
        sa.Column("max_hr", sa.Integer),
        sa.Column("avg_pace_sec_per_km", sa.REAL),
        sa.Column("adjusted_pace_sec_per_km", sa.REAL),
        sa.Column("calories", sa.Integer),
        sa.Column("training_load", sa.REAL),
        sa.Column("aerobic_te", sa.REAL),
        sa.Column("anaerobic_te", sa.REAL),
        sa.Column("duplicate_of", sa.Integer, sa.ForeignKey("activities.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_activities_user_start", "activities", ["user_id", sa.text("start_time DESC")])
    op.create_table(
        "daily_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_date", sa.Date, nullable=False),
        sa.Column("source_provider", sa.Text, nullable=False),
        sa.Column("resting_hr", sa.Integer),
        sa.Column("hrv_ms", sa.REAL),
        sa.Column("hrv_baseline_ms", sa.REAL),
        sa.Column("hrv_status", sa.Text),
        sa.Column("training_load_short", sa.REAL),
        sa.Column("training_load_long", sa.REAL),
        sa.Column("load_ratio", sa.REAL),
        sa.Column("recovery_percent", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "metric_date", "source_provider", name="uq_daily_metrics_user_date_provider"),
    )


def downgrade() -> None:
    op.drop_table("daily_metrics")
    op.drop_index("idx_activities_user_start", table_name="activities")
    op.drop_table("activities")
    op.drop_table("athlete_connections")
