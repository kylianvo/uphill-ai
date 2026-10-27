"""merge b-race and long-day-format heads

Revision ID: f3a8d1c6b2e9
Revises: d1b7a3c9e2f4, e6c2a9f4b1d7
Create Date: 2026-10-27

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f3a8d1c6b2e9"
down_revision: str | Sequence[str] | None = ("d1b7a3c9e2f4", "e6c2a9f4b1d7")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
