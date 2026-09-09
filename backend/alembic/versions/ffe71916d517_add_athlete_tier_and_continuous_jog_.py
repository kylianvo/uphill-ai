"""add athlete tier and continuous jog metric

Three columns supporting tier-aware plan generation:

- users.max_continuous_jog_min -- the longest unbroken jog in minutes. This is the
  beginner progression metric: it is the one number a new runner can feel and retell
  ("I ran 10 minutes without stopping"), and it gives adapt-week a knob to turn other
  than weekly kilometres. NULL means unknown (never asked, or not a beginner).

- workouts.walk_interval_value -- the WALK recovery per rep on a Walk/Run session. The
  three existing interval_* columns describe the work interval; without its walk partner
  a run/walk session cannot be rendered as "5 x 2 min jog / 1 min walk" and its structure
  survives only as prose in the description.

- plans.athlete_tier -- an explicit tier override for one plan. NULL means derive the
  tier from the athlete's data. It lives on the plan rather than the user because the
  same athlete can hold a start-running plan and a race plan at the same time, and the
  tier has to follow the plan's goal, not the person.

All three are nullable with no server default: absent means "unknown / derive it", which is
a meaningful state here and not the same as any particular value.

Revision ID: ffe71916d517
Revises: c1d2e3f4a5b6
Create Date: 2026-09-09 14:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ffe71916d517"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("max_continuous_jog_min", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("athlete_tier", sa.Text(), nullable=True))
    op.add_column("workouts", sa.Column("walk_interval_value", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "walk_interval_value")
    op.drop_column("plans", "athlete_tier")
    op.drop_column("users", "max_continuous_jog_min")
