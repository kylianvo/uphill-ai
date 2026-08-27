"""add gender height weight to users

Revision ID: a023ef42dde9
Revises: 970cde28af12
Create Date: 2026-08-27 17:37:04.509404

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a023ef42dde9"
down_revision: str | Sequence[str] | None = "970cde28af12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("gender", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("height_cm", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("weight_kg", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "weight_kg")
    op.drop_column("users", "height_cm")
    op.drop_column("users", "gender")
