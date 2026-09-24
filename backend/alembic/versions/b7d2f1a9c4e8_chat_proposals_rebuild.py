"""chat_proposals: rebuild kind, draft, generating/failed statuses; chat_daily_usage.rebuilds_count (Coach Chat 4b)

Revision ID: b7d2f1a9c4e8
Revises: 9a1c4e7b2d30
Create Date: 2026-09-24 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b7d2f1a9c4e8"
down_revision: str | Sequence[str] | None = "9a1c4e7b2d30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_STATUSES = "status IN ('generating', 'proposed', 'applied', 'discarded', 'stale', 'failed')"
_OLD_STATUSES = "status IN ('proposed', 'applied', 'discarded', 'stale')"


def upgrade() -> None:
    op.add_column("chat_proposals", sa.Column("kind", sa.Text(), nullable=False, server_default="schedule"))
    op.create_check_constraint("chk_chat_proposals_kind", "chat_proposals", "kind IN ('schedule', 'rebuild')")
    op.drop_constraint("chk_chat_proposals_status", "chat_proposals", type_="check")
    op.create_check_constraint("chk_chat_proposals_status", "chat_proposals", _NEW_STATUSES)
    op.add_column("chat_proposals", sa.Column("draft", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("chat_daily_usage", sa.Column("rebuilds_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("chat_daily_usage", "rebuilds_count")
    op.execute("DELETE FROM chat_proposals WHERE kind = 'rebuild' OR status IN ('generating', 'failed')")
    op.drop_column("chat_proposals", "draft")
    op.drop_constraint("chk_chat_proposals_status", "chat_proposals", type_="check")
    op.create_check_constraint("chk_chat_proposals_status", "chat_proposals", _OLD_STATUSES)
    op.drop_constraint("chk_chat_proposals_kind", "chat_proposals", type_="check")
    op.drop_column("chat_proposals", "kind")
