"""coros_plan_links: standalone mode (mode, scheduled; plan fields nullable)

Revision ID: d3f7b9a1c5e2
Revises: c8e2a4f6b1d3
Create Date: 2026-09-25 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d3f7b9a1c5e2"
down_revision: str | Sequence[str] | None = "c8e2a4f6b1d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("coros_plan_links", sa.Column("mode", sa.Text(), nullable=False, server_default="plan"))
    op.add_column(
        "coros_plan_links",
        sa.Column(
            "scheduled", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )
    op.alter_column("coros_plan_links", "coros_plan_id", existing_type=sa.Text(), nullable=True)
    op.alter_column("coros_plan_links", "coros_start_date", existing_type=sa.Date(), nullable=True)
    op.alter_column("coros_plan_links", "total_weeks", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM coros_plan_links WHERE mode = 'standalone'")
    op.alter_column("coros_plan_links", "total_weeks", existing_type=sa.Integer(), nullable=False)
    op.alter_column("coros_plan_links", "coros_start_date", existing_type=sa.Date(), nullable=False)
    op.alter_column("coros_plan_links", "coros_plan_id", existing_type=sa.Text(), nullable=False)
    op.drop_column("coros_plan_links", "scheduled")
    op.drop_column("coros_plan_links", "mode")
