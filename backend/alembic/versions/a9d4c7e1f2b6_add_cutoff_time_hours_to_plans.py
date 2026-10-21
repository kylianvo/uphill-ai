"""add cutoff_time_hours to plans

Revision ID: a9d4c7e1f2b6
Revises: e2b6f4a8c1d9
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9d4c7e1f2b6"
down_revision: str | Sequence[str] | None = "e2b6f4a8c1d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("cutoff_time_hours", sa.REAL(), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "cutoff_time_hours")
