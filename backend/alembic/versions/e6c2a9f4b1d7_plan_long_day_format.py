"""A plan's long-day format: one 6-7 h mountain day or a back-to-back weekend.

Revision ID: e6c2a9f4b1d7
Revises: c5a1d8e3f702
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e6c2a9f4b1d7"
down_revision: str | Sequence[str] | None = "c5a1d8e3f702"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("long_day_format", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "long_day_format")
