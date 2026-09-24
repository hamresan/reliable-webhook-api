from reliable_webhook_api.application.dto.operations import EventPageOutput
from reliable_webhook_api.application.operations.event_output_mapper import OperationalEventMapper
from reliable_webhook_api.application.ports import EventQuery
from reliable_webhook_api.domain import EventStatus


class ListEvents:
    def __init__(self, query: EventQuery, mapper: OperationalEventMapper) -> None:
        self._query = query
        self._mapper = mapper

    async def execute(
        self,
        status: EventStatus | None,
        offset: int,
        limit: int,
    ) -> EventPageOutput:
        page = await self._query.page(status, offset, limit)
        return EventPageOutput(
            items=tuple(self._mapper.to_output(event) for event in page.items),
            total=page.total,
            offset=offset,
            limit=limit,
        )
