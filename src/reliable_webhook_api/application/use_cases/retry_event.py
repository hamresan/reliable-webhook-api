from reliable_webhook_api.application.dto.operations import RetryEventOutput
from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.application.ports import EventRepository, UnitOfWork
from reliable_webhook_api.application.retries import RetryCoordinator
from reliable_webhook_api.domain import EventId, RetryNotAllowedError


class RetryEvent:
    def __init__(
        self,
        repository: EventRepository,
        unit_of_work: UnitOfWork,
        retry_coordinator: RetryCoordinator,
    ) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work
        self._retry_coordinator = retry_coordinator

    async def execute(self, event_id: EventId) -> RetryEventOutput:
        async with self._unit_of_work:
            event = await self._repository.get(event_id)
            if event is None:
                raise NotFoundError("Webhook event was not found.")

            try:
                retry_at = await self._retry_coordinator.schedule(event)
            except RetryNotAllowedError as exc:
                raise InvalidTransitionError(str(exc)) from exc

        return RetryEventOutput(event_id=event.id.value, status=event.status, retry_at=retry_at)
