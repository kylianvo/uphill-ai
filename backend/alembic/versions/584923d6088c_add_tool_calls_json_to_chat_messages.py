"""add tool_calls_json to chat_messages

Revision ID: 584923d6088c
Revises: bab9f573a00c
Create Date: 2026-09-22 20:18:20.787133

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "584923d6088c"
down_revision: str | Sequence[str] | None = "bab9f573a00c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column("tool_calls_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "tool_calls_json")
