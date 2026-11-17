"""Encrypted OAuth state and provider delivery tracking."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "integrations",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "deliveries",
        sa.Column("id", sa.String(36), sa.ForeignKey("outbox.id"), primary_key=True),
        sa.Column("provider_id", sa.String(100), nullable=False),
        sa.Column("thread_id", sa.String(100), nullable=False),
        sa.Column("replied", sa.Boolean(), nullable=False),
        sa.Column("event", sa.String(40), nullable=False),
    )
    op.create_index("ix_deliveries_thread_id", "deliveries", ["thread_id"])


def downgrade():
    op.drop_table("deliveries")
    op.drop_table("integrations")
