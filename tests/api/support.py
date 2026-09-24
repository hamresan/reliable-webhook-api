import hashlib
import hmac

from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import InMemoryEventRepository, NoopTransaction
from reliable_webhook_api.infrastructure.security import HmacSha256SignatureVerifier


def sign(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def build_receive_use_case(
    repository: InMemoryEventRepository,
    secret: str,
) -> ReceiveWebhookEvent:
    return ReceiveWebhookEvent(
        repository=repository,
        signature_verifier=HmacSha256SignatureVerifier(secret),
        clock=SystemClock(),
        transaction=NoopTransaction(),
    )
