"""add coros_plan_links and coros_push_usage (COROS push to watch)

Revision ID: c8e2a4f6b1d3
Revises: b7d2f1a9c4e8
Create Date: 2026-09-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c8e2a4f6b1d3"
down_revision: str | Sequence[str] | None = "b7d2f1a9c4e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coros_plan_links",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("coros_plan_id", sa.Text(), nullable=False),
        sa.Column("coros_start_date", sa.Date(), nullable=False),
        sa.Column("total_weeks", sa.Integer(), nullable=False),
        sa.Column("window_end", sa.Date(), nullable=False),
        sa.Column(
            "day_hashes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("last_pushed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("partial", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_table(
        "coros_push_usage",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("usage_date", sa.Date(), primary_key=True),
        sa.Column("pushes", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("coros_push_usage")
    op.drop_table("coros_plan_links")
