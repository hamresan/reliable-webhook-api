from reliable_webhook_api.application.dto.operations import RetryEventOutput
from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.application.ports import (
    Clock,
    EventRepository,
    RetryScheduler,
    UnitOfWork,
)
from reliable_webhook_api.domain import (
    AttemptNumber,
    EventId,
    EventStatus,
    EventTransitionPolicy,
    ExponentialBackoff,
    RetryableFailurePolicy,
    RetryNotAllowedError,
    RetryPolicy,
)


class RetryEvent:
    def __init__(
        self,
        repository: EventRepository,
        scheduler: RetryScheduler,
        clock: Clock,
        unit_of_work: UnitOfWork,
        retry_policy: RetryPolicy,
        retryable_failures: RetryableFailurePolicy,
        backoff: ExponentialBackoff,
        transition_policy: EventTransitionPolicy,
    ) -> None:
        self._repository = repository
        self._scheduler = scheduler
        self._clock = clock
        self._unit_of_work = unit_of_work
        self._retry_policy = retry_policy
        self._retryable_failures = retryable_failures
        self._backoff = backoff
        self._transition_policy = transition_policy

    async def execute(self, event_id: EventId) -> RetryEventOutput:
        async with self._unit_of_work:
            event = await self._repository.get(event_id)
            if event is None:
                raise NotFoundError("Webhook event was not found.")

            attempt_number = AttemptNumber(max(1, len(event.attempts)))
            try:
                self._retry_policy.ensure_allowed(event.status, attempt_number)
            except RetryNotAllowedError as exc:
                raise InvalidTransitionError(str(exc)) from exc

            if not self._retryable_failures.is_retryable(event.failure_reason):
                raise InvalidTransitionError("Event failure is not retryable.")

            retry_at = self._clock.now() + self._backoff.delay_for(attempt_number)
            self._transition_policy.ensure_allowed(event.status, EventStatus.RETRY_SCHEDULED)
            event.status = EventStatus.RETRY_SCHEDULED
            event.next_retry_at = retry_at
            await self._repository.save(event)
            await self._scheduler.schedule(event.id, retry_at)

        return RetryEventOutput(event_id=event.id.value, status=event.status, retry_at=retry_at)
