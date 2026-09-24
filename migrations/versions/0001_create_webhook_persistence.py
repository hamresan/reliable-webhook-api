"""Create webhook event persistence tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("failure_code", sa.String(length=255), nullable=True),
        sa.Column("failure_message", sa.String(length=2000), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint("event_id", name="uq_webhook_events_event_id"),
    )
    op.create_index("ix_webhook_events_status", "webhook_events", ["status"])
    op.create_table(
        "processing_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=255), nullable=True),
        sa.Column("failure_message", sa.String(length=2000), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["webhook_events.event_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "number", name="uq_processing_attempt_event_number"),
    )
    op.create_index("ix_processing_attempts_event_id", "processing_attempts", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_processing_attempts_event_id", table_name="processing_attempts")
    op.drop_table("processing_attempts")
    op.drop_index("ix_webhook_events_status", table_name="webhook_events")
    op.drop_table("webhook_events")
