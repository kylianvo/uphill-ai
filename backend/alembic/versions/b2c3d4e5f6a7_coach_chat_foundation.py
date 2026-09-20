"""add coach chat foundation tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-09-20 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("summarized_through_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_chat_threads_user_id", "chat_threads", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "thread_id",
            sa.Integer(),
            sa.ForeignKey("chat_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("lang", sa.Text(), nullable=False, server_default="en"),
        sa.Column("status", sa.Text(), nullable=False, server_default="ok"),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("citations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prompt_name", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("usage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="chk_chat_messages_role"),
        sa.CheckConstraint("status IN ('ok', 'error', 'interrupted')", name="chk_chat_messages_status"),
    )
    op.create_index(
        "idx_chat_messages_thread_created",
        "chat_messages",
        ["thread_id", sa.text("created_at DESC")],
    )

    op.create_foreign_key(
        "fk_chat_threads_summarized_through",
        "chat_threads",
        "chat_messages",
        ["summarized_through_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "chat_turns",
        sa.Column("request_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            sa.Integer(),
            sa.ForeignKey("chat_threads.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column(
            "root_turn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_turns.request_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column(
            "result_message_id",
            sa.Integer(),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('active', 'ok', 'error', 'interrupted', 'cleared')",
            name="chk_chat_turns_status",
        ),
    )
    op.create_index(
        "idx_chat_turns_user_created",
        "chat_turns",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index("idx_chat_turns_root", "chat_turns", ["root_turn_id"])

    op.create_table(
        "chat_daily_usage",
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("new_turns_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retries_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("usage_date", "user_id", name="pk_chat_daily_usage"),
    )

    op.create_table(
        "chat_llm_calls",
        sa.Column("call_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_turns.request_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("feature", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("usage_known", sa.Boolean(), nullable=False, server_default="FALSE"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("thinking_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="reserved"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('reserved', 'ok', 'error', 'unknown')",
            name="chk_chat_llm_calls_status",
        ),
    )
    op.create_index("idx_chat_llm_calls_request_id", "chat_llm_calls", ["request_id"])


def downgrade() -> None:
    op.drop_index("idx_chat_llm_calls_request_id", table_name="chat_llm_calls")
    op.drop_table("chat_llm_calls")
    op.drop_table("chat_daily_usage")
    op.drop_index("idx_chat_turns_root", table_name="chat_turns")
    op.drop_index("idx_chat_turns_user_created", table_name="chat_turns")
    op.drop_table("chat_turns")
    op.drop_constraint("fk_chat_threads_summarized_through", "chat_threads", type_="foreignkey")
    op.drop_index("idx_chat_messages_thread_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("idx_chat_threads_user_id", table_name="chat_threads")
    op.drop_table("chat_threads")
