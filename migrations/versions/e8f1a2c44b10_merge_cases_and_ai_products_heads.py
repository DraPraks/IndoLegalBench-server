"""merge cases and ai_products heads

Revision ID: e8f1a2c44b10
Revises: b7e4c1a09d22, c3a91e7b4d02
Create Date: 2026-09-28 18:30:00.000000

Both revisions descend from a4c8e2b17d90. This empty revision gives
alembic upgrade head a single tip.
"""

from collections.abc import Sequence

revision: str = "e8f1a2c44b10"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = ("b7e4c1a09d22", "c3a91e7b4d02")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
