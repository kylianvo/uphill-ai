"""add chat_proposals (Coach Chat sub-project 4a)

Revision ID: 9a1c4e7b2d30
Revises: 584923d6088c
Create Date: 2026-09-23 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "9a1c4e7b2d30"
down_revision: str | Sequence[str] | None = "584923d6088c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fingerprints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="proposed"),
        sa.Column("stale_reason", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('proposed', 'applied', 'discarded', 'stale')", name="chk_chat_proposals_status"),
    )
    op.create_index("idx_chat_proposals_thread", "chat_proposals", ["thread_id"])
    op.create_index("idx_chat_proposals_user_status", "chat_proposals", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_chat_proposals_user_status", table_name="chat_proposals")
    op.drop_index("idx_chat_proposals_thread", table_name="chat_proposals")
    op.drop_table("chat_proposals")
