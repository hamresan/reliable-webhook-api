from datetime import datetime
from typing import Protocol

from reliable_webhook_api.domain import WebhookEvent


class DueRetryReader(Protocol):
    async def due_retries(self, due_at: datetime, limit: int) -> list[WebhookEvent]: ...
