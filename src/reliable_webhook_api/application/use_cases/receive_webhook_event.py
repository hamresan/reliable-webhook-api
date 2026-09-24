from reliable_webhook_api.application.dto import EventOutput, ReceiveWebhookEventInput
from reliable_webhook_api.application.errors import InvalidSignatureError, ValidationError
from reliable_webhook_api.application.ports import Clock, EventRepository, SignatureVerifier, Transaction
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    ExternalEventId,
    ProviderName,
    ReceivedAt,
    WebhookEvent,
)


class ReceiveWebhookEvent:
    def __init__(
        self,
        repository: EventRepository,
        signature_verifier: SignatureVerifier,
        clock: Clock,
        transaction: Transaction,
    ) -> None:
        self._repository = repository
        self._signature_verifier = signature_verifier
        self._clock = clock
        self._transaction = transaction

    async def execute(self, request: ReceiveWebhookEventInput) -> EventOutput:
        signature = request.signature
        if not signature or not self._signature_verifier.verify(request.raw_payload, signature):
            raise InvalidSignatureError("Invalid webhook signature.")

        event_input = request.event
        if event_input is None:
            raise ValidationError("Invalid webhook event envelope.")

        try:
            event_id = EventId(event_input.event_id)
            event_type = EventType(event_input.event_type)
            occurred_at = event_input.occurred_at
            if occurred_at.tzinfo is None:
                raise ValueError("Occurred timestamp must be timezone-aware.")
        except ValueError as exc:
            raise ValidationError("Invalid webhook event envelope.") from exc

        async with self._transaction:
            existing = await self._repository.get(event_id)
            if existing is not None:
                return EventOutput(
                    event_id=existing.id.value,
                    status=existing.status,
                    duplicate=True,
                )

            event = WebhookEvent(
                id=event_id,
                provider=ProviderName("generic"),
                external_event_id=ExternalEventId(str(event_input.event_id)),
                event_type=event_type,
                payload={
                    "occurred_at": occurred_at.isoformat(),
                    "data": event_input.data,
                },
                status=EventStatus.RECEIVED,
                received_at=ReceivedAt(self._clock.now()),
            )
            await self._repository.add(event)

        return EventOutput(event_id=event.id.value, status=event.status, duplicate=False)
