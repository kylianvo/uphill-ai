"""Garmin Body Battery and stress on daily_metrics; Garmin VO2 max on users."""

import sqlalchemy as sa

from alembic import op

revision = "e3a9c7d1f4b2"
down_revision = "d7e1b3c5a2f9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("daily_metrics", sa.Column("body_battery_high", sa.Integer(), nullable=True))
    op.add_column("daily_metrics", sa.Column("stress_avg", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("garmin_vo2max", sa.REAL(), nullable=True))


def downgrade():
    op.drop_column("users", "garmin_vo2max")
    op.drop_column("daily_metrics", "stress_avg")
    op.drop_column("daily_metrics", "body_battery_high")
