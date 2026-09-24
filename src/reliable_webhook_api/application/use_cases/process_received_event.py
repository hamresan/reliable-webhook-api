from reliable_webhook_api.application.dto.process_event import ProcessEventOutput
from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.application.ports import (
    Clock,
    EventProcessor,
    EventRepository,
    UnitOfWork,
)
from reliable_webhook_api.application.processing import ProcessingFailureMapper
from reliable_webhook_api.domain import (
    AttemptNumber,
    EventId,
    EventStatus,
    EventTransitionPolicy,
    FailureReason,
    InvalidEventTransitionError,
    ProcessingAttempt,
    ProcessingPeriod,
    ProcessingTimestamp,
)


class ProcessReceivedEvent:
    def __init__(
        self,
        repository: EventRepository,
        processor: EventProcessor,
        clock: Clock,
        unit_of_work: UnitOfWork,
        transition_policy: EventTransitionPolicy,
        failure_mapper: ProcessingFailureMapper,
    ) -> None:
        self._repository = repository
        self._processor = processor
        self._clock = clock
        self._unit_of_work = unit_of_work
        self._transition_policy = transition_policy
        self._failure_mapper = failure_mapper

    async def execute(self, event_id: EventId) -> ProcessEventOutput:
        async with self._unit_of_work:
            event = await self._repository.get(event_id)
            if event is None:
                raise NotFoundError("Webhook event was not found.")

            try:
                self._transition_policy.ensure_allowed(event.status, EventStatus.PROCESSING)
            except InvalidEventTransitionError as exc:
                raise InvalidTransitionError(str(exc)) from exc

            event.status = EventStatus.PROCESSING
            event.next_retry_at = None
            await self._repository.save(event)

            started_at = ProcessingTimestamp(self._clock.now())
            failure_reason: FailureReason | None = None
            try:
                await self._processor.process(event)
                target_status = EventStatus.PROCESSED
            except Exception as exc:
                target_status = EventStatus.FAILED
                failure_reason = self._failure_mapper.from_exception(exc)

            finished_at = ProcessingTimestamp(self._clock.now())
            self._transition_policy.ensure_allowed(event.status, target_status)
            event.status = target_status
            event.failure_reason = failure_reason
            event.attempts.append(
                ProcessingAttempt(
                    number=AttemptNumber(len(event.attempts) + 1),
                    period=ProcessingPeriod(started_at=started_at, finished_at=finished_at),
                    failure_reason=failure_reason,
                )
            )
            await self._repository.save(event)

        return ProcessEventOutput(event_id=event.id.value, status=event.status)
