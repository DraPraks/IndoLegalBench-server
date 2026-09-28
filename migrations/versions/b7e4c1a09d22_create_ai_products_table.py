"""create ai_products table

Revision ID: b7e4c1a09d22
Revises: a4c8e2b17d90
Create Date: 2026-09-28 23:55:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7e4c1a09d22"  # pragma: allowlist secret
down_revision: str | None = "a4c8e2b17d90"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# create_type=False: tipe dibuat sekali lewat .create(). CREATE TABLE tidak
# boleh mengeluarkan CREATE TYPE lagi; PostgreSQL menolak duplikat itu di
# dalam transaksi Alembic yang sama. SQLite mengabaikan CREATE/DROP TYPE.
provider_type_enum = postgresql.ENUM(
    "openai_compatible",
    "custom_http",
    name="ai_product_provider_type_enum",
    create_type=False,
)
last_test_status_enum = postgresql.ENUM(
    "ok",
    "failed",
    name="ai_product_last_test_status_enum",
    create_type=False,
)


def upgrade() -> None:
    provider_type_enum.create(op.get_bind(), checkfirst=True)
    last_test_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "ai_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("provider_type", provider_type_enum, nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column("credential_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("credential_hint", sa.String(length=4), nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False),
        sa.Column("monthly_budget_idr", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_status", last_test_status_enum, nullable=True),
        sa.Column("last_test_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rate_limit_per_minute > 0",
            name="ck_ai_products_rate_limit_positive",
        ),
        sa.CheckConstraint(
            "monthly_budget_idr > 0",
            name="ck_ai_products_monthly_budget_positive",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_ai_products_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_ai_products_name"),
    )


def downgrade() -> None:
    op.drop_table("ai_products")
    last_test_status_enum.drop(op.get_bind(), checkfirst=True)
    provider_type_enum.drop(op.get_bind(), checkfirst=True)
