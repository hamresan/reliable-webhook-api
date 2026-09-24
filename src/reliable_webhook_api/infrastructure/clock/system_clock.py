from datetime import UTC, datetime

from reliable_webhook_api.application.ports import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
