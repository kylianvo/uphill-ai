"""users.ai_eval_excluded: keep Garmin-connected users out of AI evaluation (Agreement §15.11)."""

import sqlalchemy as sa

from alembic import op

revision = "c4d8e2f1a9b7"
down_revision = "a6f2c8d9e104"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("ai_eval_excluded", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column("users", "ai_eval_excluded")
