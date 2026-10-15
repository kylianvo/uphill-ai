"""daily_metrics.sleep_minutes, merging the two heads

Apple Health recovery metrics (sub-project B): asleep minutes for the night that
ends on metric_date. Also merges the race_result_location and
profile_field_sources heads, which both branched off d5f8b2c4e7a1.

Revision ID: b3d9f1a6c2e4
Revises: a713c9e6f024, a7c4e2f9b1d3
Create Date: 2026-10-14 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3d9f1a6c2e4"
down_revision: str | Sequence[str] | None = ("a713c9e6f024", "a7c4e2f9b1d3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("daily_metrics", sa.Column("sleep_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("daily_metrics", "sleep_minutes")
