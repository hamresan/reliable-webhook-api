from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reliable_webhook_api.infrastructure.persistence.models.base import Base


class EventModel(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_webhook_events_event_id"),)

    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    failure_code: Mapped[str | None] = mapped_column(String(255))
    failure_message: Mapped[str | None] = mapped_column(String(2000))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    attempts: Mapped[list["ProcessingAttemptModel"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="ProcessingAttemptModel.number",
        lazy="selectin",
    )
