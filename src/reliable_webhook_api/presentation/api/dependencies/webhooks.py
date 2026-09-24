from functools import lru_cache

from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent
from reliable_webhook_api.config import get_settings
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import InMemoryEventRepository, NoopTransaction
from reliable_webhook_api.infrastructure.security import HmacSha256SignatureVerifier


@lru_cache
def get_repository() -> InMemoryEventRepository:
    return InMemoryEventRepository()


def get_receive_webhook_event() -> ReceiveWebhookEvent:
    settings = get_settings()
    return ReceiveWebhookEvent(
        repository=get_repository(),
        signature_verifier=HmacSha256SignatureVerifier(settings.webhook_secret),
        clock=SystemClock(),
        transaction=NoopTransaction(),
    )
