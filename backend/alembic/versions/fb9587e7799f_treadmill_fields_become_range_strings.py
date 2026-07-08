"""treadmill fields become range strings

Revision ID: fb9587e7799f
Revises: 9045bc8b836f
Create Date: 2026-07-09 00:24:20.424660

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "fb9587e7799f"
down_revision: str | Sequence[str] | None = "9045bc8b836f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Treadmill settings become deterministic range strings ("8.2-9.2" kph,
    # "7.3-9.3" %) derived from each workout's own target_pace; existing
    # numeric values cast losslessly to their text form.
    op.alter_column(
        "workouts",
        "treadmill_incline",
        type_=sa.Text(),
        server_default="0",
        postgresql_using="treadmill_incline::text",
    )
    op.alter_column(
        "workouts",
        "treadmill_speed",
        type_=sa.Text(),
        server_default="0",
        postgresql_using="treadmill_speed::text",
    )


def downgrade() -> None:
    # Range strings collapse to their lower bound when reverting to REAL.
    op.alter_column(
        "workouts",
        "treadmill_incline",
        type_=sa.REAL(),
        server_default="0.0",
        postgresql_using="NULLIF(split_part(treadmill_incline, '-', 1), '')::real",
    )
    op.alter_column(
        "workouts",
        "treadmill_speed",
        type_=sa.REAL(),
        server_default="0.0",
        postgresql_using="NULLIF(split_part(treadmill_speed, '-', 1), '')::real",
    )
