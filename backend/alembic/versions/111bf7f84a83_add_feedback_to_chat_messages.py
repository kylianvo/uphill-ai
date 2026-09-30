"""add feedback to chat_messages

Revision ID: 111bf7f84a83
Revises: a7c3e9d1f2b4
Create Date: 2026-09-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "111bf7f84a83"
down_revision: str | Sequence[str] | None = "a7c3e9d1f2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Athlete thumbs on a coach reply; NULL = no vote. Mirrored to Langfuse as the "thumbs" score.
    op.add_column(
        "chat_messages",
        sa.Column("feedback", sa.SmallInteger(), sa.CheckConstraint("feedback IN (-1, 1)"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "feedback")
