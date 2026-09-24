from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reliable_webhook_api.infrastructure.persistence.models.base import Base


class ProcessingAttemptModel(Base):
    __tablename__ = "processing_attempts"
    __table_args__ = (
        UniqueConstraint("event_id", "number", name="uq_processing_attempt_event_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("webhook_events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(255))
    failure_message: Mapped[str | None] = mapped_column(String(2000))

    event: Mapped["EventModel"] = relationship(back_populates="attempts")
