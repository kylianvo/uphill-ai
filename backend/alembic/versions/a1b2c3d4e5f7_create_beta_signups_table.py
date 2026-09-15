"""create beta_signups table

Revision ID: a1b2c3d4e5f7
Revises: afceaab86d5d
Create Date: 2026-09-15 09:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f7"
down_revision: str | Sequence[str] | None = "afceaab86d5d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "beta_signups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("referral_source", sa.String(length=100), nullable=False),
        sa.Column("usage_intent", sa.String(length=100), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_beta_signups_email", "beta_signups", ["email"])
    op.create_index("idx_beta_signups_created_at", "beta_signups", [sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_index("idx_beta_signups_created_at", table_name="beta_signups")
    op.drop_index("idx_beta_signups_email", table_name="beta_signups")
    op.drop_table("beta_signups")
