"""Add nullable sync idempotency key and backfill legacy rows.

Revision ID: 7b1f3f1c2a01
Revises: 03e87da238c7
"""

from alembic import op
import sqlalchemy as sa

revision = "7b1f3f1c2a01"
down_revision = "03e87da238c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sync_logs",
        sa.Column("idempotency_key", sa.String(length=160), nullable=True),
    )
    # Existing rows need deterministic, unique identifiers before NOT NULL and
    # uniqueness are enforced by the following revision.
    op.execute(
        "UPDATE sync_logs "
        "SET idempotency_key = 'legacy-sync-' || CAST(id AS VARCHAR) "
        "WHERE idempotency_key IS NULL OR idempotency_key = ''"
    )


def downgrade() -> None:
    op.drop_column("sync_logs", "idempotency_key")
