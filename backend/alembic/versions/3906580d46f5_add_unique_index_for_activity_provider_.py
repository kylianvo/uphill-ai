"""add unique index for activity provider external id

Revision ID: 3906580d46f5
Revises: b1c2d3e4f5a6
Create Date: 2026-09-05
"""

from collections.abc import Sequence

from alembic import op

revision: str = "3906580d46f5"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enforces upsert_activity's (provider, external_id) idempotency at the
    # database level. The app-level pre-check SELECT it also does is only an
    # optimization: two concurrent callers for the same provider (a manual
    # "sync now" racing the hourly cron sweep) can both pass that SELECT
    # before either has committed its INSERT, which would otherwise leave two
    # real rows for one run. Rows whose external_ids has no key for their own
    # source_provider get NULL for the third column, and Postgres never
    # treats NULLs as duplicates of each other, so those stay unrestricted.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_provider_external
        ON activities (user_id, source_provider, (external_ids ->> source_provider))
        """)


def downgrade() -> None:
    op.drop_index("idx_activities_provider_external", table_name="activities")
