from datetime import datetime

from reliable_webhook_api.application.ports import Clock, EventRepository, RetryScheduler
from reliable_webhook_api.domain import (
    AttemptNumber,
    EventStatus,
    EventTransitionPolicy,
    ExponentialBackoff,
    RetryableFailurePolicy,
    RetryNotAllowedError,
    RetryPolicy,
    WebhookEvent,
)


class RetryCoordinator:
    def __init__(
        self,
        repository: EventRepository,
        scheduler: RetryScheduler,
        clock: Clock,
        retry_policy: RetryPolicy,
        retryable_failures: RetryableFailurePolicy,
        backoff: ExponentialBackoff,
        transition_policy: EventTransitionPolicy,
    ) -> None:
        self._repository = repository
        self._scheduler = scheduler
        self._clock = clock
        self._retry_policy = retry_policy
        self._retryable_failures = retryable_failures
        self._backoff = backoff
        self._transition_policy = transition_policy

    async def schedule(self, event: WebhookEvent) -> datetime:
        attempt_number = AttemptNumber(max(1, len(event.attempts)))
        self._retry_policy.ensure_allowed(event.status, attempt_number)
        if not self._retryable_failures.is_retryable(event.failure_reason):
            raise RetryNotAllowedError(event.status, attempt_number)

        retry_at = self._clock.now() + self._backoff.delay_for(attempt_number)
        self._transition_policy.ensure_allowed(event.status, EventStatus.RETRY_SCHEDULED)
        event.status = EventStatus.RETRY_SCHEDULED
        event.next_retry_at = retry_at
        await self._repository.schedule_retry(event.id, retry_at)
        await self._scheduler.schedule(event.id, retry_at)
        return retry_at

    async def schedule_if_allowed(self, event: WebhookEvent) -> datetime | None:
        try:
            return await self.schedule(event)
        except RetryNotAllowedError:
            return None
