from reliable_webhook_api.application.dto import EventOutput, ReceiveWebhookEventInput
from reliable_webhook_api.application.errors import (
    DuplicateEventError,
    InvalidSignatureError,
    ValidationError,
)
from reliable_webhook_api.application.ports import (
    Clock,
    EventRepository,
    SignatureVerifier,
    UnitOfWork,
)
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    OccurredAt,
    ReceivedAt,
    WebhookEvent,
)


class ReceiveWebhookEvent:
    def __init__(
        self,
        repository: EventRepository,
        signature_verifier: SignatureVerifier,
        clock: Clock,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._signature_verifier = signature_verifier
        self._clock = clock
        self._unit_of_work = unit_of_work

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
            occurred_at = OccurredAt(event_input.occurred_at)
        except ValueError as exc:
            raise ValidationError("Invalid webhook event envelope.") from exc

        try:
            async with self._unit_of_work:
                existing = await self._repository.get(event_id)
                if existing is not None:
                    return self._duplicate_output(existing)

                event = WebhookEvent(
                    id=event_id,
                    event_type=event_type,
                    occurred_at=occurred_at,
                    data=event_input.data,
                    status=EventStatus.RECEIVED,
                    received_at=ReceivedAt(self._clock.now()),
                )
                await self._repository.add(event)
        except DuplicateEventError:
            existing = await self._repository.get(event_id)
            if existing is None:
                raise
            return self._duplicate_output(existing)

        return EventOutput(event_id=event.id.value, status=event.status, duplicate=False)

    @staticmethod
    def _duplicate_output(event: WebhookEvent) -> EventOutput:
        return EventOutput(event_id=event.id.value, status=event.status, duplicate=True)
