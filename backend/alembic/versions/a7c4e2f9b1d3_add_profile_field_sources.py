"""add users.profile_field_sources

Where each coach-editable physiology/pace number came from. A JSONB map keyed by
users column name (max_hr, resting_hr, aet_hr, ant_hr, zone2_pace_min,
zone2_pace_max, threshold_pace) to {"source": "coach"|"athlete", "by_name", "at",
"previous", "seen"}. A field with no entry is resolved at read time (athlete-set
if the column has a value, else an app default). "seen" drives the athlete's
"your coach updated your zones" card. NULL = no recorded edits.

Revision ID: a7c4e2f9b1d3
Revises: d5f8b2c4e7a1
Create Date: 2026-10-09 23:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a7c4e2f9b1d3"
down_revision: str | Sequence[str] | None = "d5f8b2c4e7a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("profile_field_sources", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "profile_field_sources")
