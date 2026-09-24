from reliable_webhook_api.application.dto.operations import OperationalEventOutput
from reliable_webhook_api.application.errors import NotFoundError
from reliable_webhook_api.application.operations.event_output_mapper import OperationalEventMapper
from reliable_webhook_api.application.ports import EventQuery
from reliable_webhook_api.domain import EventId


class GetEvent:
    def __init__(self, query: EventQuery, mapper: OperationalEventMapper) -> None:
        self._query = query
        self._mapper = mapper

    async def execute(self, event_id: EventId) -> OperationalEventOutput:
        event = await self._query.get(event_id)
        if event is None:
            raise NotFoundError("Webhook event was not found.")
        return self._mapper.to_output(event)
