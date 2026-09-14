"""add ai narrative fields to block_reviews

Two Gemini-authored narrative columns on block_reviews, populated when the next
block is generated: ai_last_week_review reviews the block that just finished,
ai_this_week_description describes the block just generated. Distinct from the
existing overall_rpe/notes columns, which the athlete submits themselves.

Revision ID: afceaab86d5d
Revises: ffe71916d517
Create Date: 2026-09-14 21:57:32.873593

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "afceaab86d5d"
down_revision: str | Sequence[str] | None = "ffe71916d517"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("block_reviews", sa.Column("ai_last_week_review", sa.Text(), nullable=True))
    op.add_column("block_reviews", sa.Column("ai_this_week_description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("block_reviews", "ai_this_week_description")
    op.drop_column("block_reviews", "ai_last_week_review")
