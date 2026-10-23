"""progress tab: sleep window, HRV normal range, long-run HR drift

Revision ID: b3f7d2e9a4c1
Revises: a9d4c7e1f2b6
Create Date: 2026-10-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3f7d2e9a4c1"
down_revision: str | Sequence[str] | None = "a9d4c7e1f2b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("daily_metrics", sa.Column("sleep_start", sa.Time(), nullable=True))
    op.add_column("daily_metrics", sa.Column("sleep_end", sa.Time(), nullable=True))
    op.add_column("daily_metrics", sa.Column("hrv_range_low", sa.REAL(), nullable=True))
    op.add_column("daily_metrics", sa.Column("hrv_range_high", sa.REAL(), nullable=True))
    op.add_column("activities", sa.Column("hr_drift_pct", sa.REAL(), nullable=True))
    op.add_column("activities", sa.Column("hr_drift_checked", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("activities", "hr_drift_checked")
    op.drop_column("activities", "hr_drift_pct")
    op.drop_column("daily_metrics", "hrv_range_high")
    op.drop_column("daily_metrics", "hrv_range_low")
    op.drop_column("daily_metrics", "sleep_end")
    op.drop_column("daily_metrics", "sleep_start")
