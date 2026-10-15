"""password_reset_codes: hashed 6-digit codes for forgot-password

Revision ID: c8e2a4f6d9b1
Revises: b3d9f1a6c2e4
Create Date: 2026-10-15 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c8e2a4f6d9b1"
down_revision: str | Sequence[str] | None = "b3d9f1a6c2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_password_reset_codes_user_created", "password_reset_codes", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_password_reset_codes_user_created", table_name="password_reset_codes")
    op.drop_table("password_reset_codes")
