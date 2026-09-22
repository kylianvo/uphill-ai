"""allow interrupted status on chat_llm_calls

Revision ID: bab9f573a00c
Revises: b2c3d4e5f6a7
Create Date: 2026-09-22 15:01:53.939408

"""

from collections.abc import Sequence

from alembic import op

revision: str = "bab9f573a00c"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("chk_chat_llm_calls_status", "chat_llm_calls", type_="check")
    op.create_check_constraint(
        "chk_chat_llm_calls_status",
        "chat_llm_calls",
        "status IN ('reserved', 'ok', 'error', 'unknown', 'interrupted')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_chat_llm_calls_status", "chat_llm_calls", type_="check")
    op.create_check_constraint(
        "chk_chat_llm_calls_status",
        "chat_llm_calls",
        "status IN ('reserved', 'ok', 'error', 'unknown')",
    )
