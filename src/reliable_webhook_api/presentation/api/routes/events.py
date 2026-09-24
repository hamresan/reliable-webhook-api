from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.application.use_cases import GetEvent, ListEvents, RetryEvent
from reliable_webhook_api.domain import EventId, EventStatus
from reliable_webhook_api.presentation.api.dependencies.operations import (
    get_event_use_case,
    get_list_events_use_case,
    get_retry_event_use_case,
)
from reliable_webhook_api.presentation.api.mappers import OperationalResponseMapper
from reliable_webhook_api.presentation.api.schemas.operations import (
    EventListResponse,
    EventResponse,
    RetryResponse,
)

router = APIRouter(prefix="/events", tags=["events"])
GetEventDependency = Annotated[GetEvent, Depends(get_event_use_case)]
ListEventsDependency = Annotated[ListEvents, Depends(get_list_events_use_case)]
RetryEventDependency = Annotated[RetryEvent, Depends(get_retry_event_use_case)]


@router.get(
    "",
    response_model=EventListResponse,
    summary="List webhook events",
    description="Filter webhook events by status and return stable offset pagination metadata.",
)
async def list_events(
    use_case: ListEventsDependency,
    status: EventStatus | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> EventListResponse:
    result = await use_case.execute(status, offset, limit)
    return EventListResponse(
        items=[OperationalResponseMapper.to_response(item) for item in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get webhook event",
    description="Return operational status, attempts, timestamps, and sanitized failure metadata.",
)
async def get_event(
    event_id: UUID,
    use_case: GetEventDependency,
) -> EventResponse | JSONResponse:
    try:
        result = await use_case.execute(EventId(event_id))
    except NotFoundError:
        return JSONResponse(status_code=404, content={"detail": "Webhook event was not found."})
    return OperationalResponseMapper.to_response(result)


@router.post(
    "/{event_id}/retry",
    response_model=RetryResponse,
    status_code=202,
    summary="Schedule webhook event retry",
    description="Schedule a bounded retry only when the failed event is explicitly retryable.",
)
async def retry_event(
    event_id: UUID,
    use_case: RetryEventDependency,
) -> RetryResponse | JSONResponse:
    try:
        result = await use_case.execute(EventId(event_id))
    except NotFoundError:
        return JSONResponse(status_code=404, content={"detail": "Webhook event was not found."})
    except InvalidTransitionError as exc:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    return RetryResponse(
        event_id=result.event_id,
        status=result.status,
        retry_at=result.retry_at,
    )
