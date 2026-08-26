"""Enforce durable sync idempotency key uniqueness.

Revision ID: 8c2d4e5f6a02
Revises: 7b1f3f1c2a01
"""

from alembic import op
import sqlalchemy as sa

revision = "8c2d4e5f6a02"
down_revision = "7b1f3f1c2a01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("sync_logs", recreate="always") as batch_op:
            batch_op.alter_column(
                "idempotency_key",
                existing_type=sa.String(length=160),
                nullable=False,
            )
    else:
        op.alter_column(
            "sync_logs",
            "idempotency_key",
            existing_type=sa.String(length=160),
            nullable=False,
        )
    op.create_index(
        "uq_sync_log_idempotency_key",
        "sync_logs",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key <> ''"),
    )


def downgrade() -> None:
    op.drop_index("uq_sync_log_idempotency_key", table_name="sync_logs")
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("sync_logs", recreate="always") as batch_op:
            batch_op.alter_column(
                "idempotency_key",
                existing_type=sa.String(length=160),
                nullable=True,
            )
    else:
        op.alter_column(
            "sync_logs",
            "idempotency_key",
            existing_type=sa.String(length=160),
            nullable=True,
        )
