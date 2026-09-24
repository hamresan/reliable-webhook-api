import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from reliable_webhook_api.application.dto import EventInput, ReceiveWebhookEventInput
from reliable_webhook_api.application.errors import InvalidSignatureError, ValidationError
from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent
from reliable_webhook_api.config import get_settings
from reliable_webhook_api.presentation.api.dependencies import get_receive_webhook_event
from reliable_webhook_api.presentation.api.schemas import WebhookEventRequest, WebhookEventResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/events",
    response_model=WebhookEventResponse,
    status_code=202,
    responses={
        400: {"description": "Invalid webhook event envelope."},
        401: {"description": "Invalid webhook signature."},
    },
)
async def receive_webhook_event(
    request: Request,
    use_case: ReceiveWebhookEvent = Depends(get_receive_webhook_event),
) -> JSONResponse:
    raw_payload = await request.body()
    signature = request.headers.get(get_settings().webhook_signature_header)

    try:
        parsed = WebhookEventRequest.model_validate_json(raw_payload)
    except (PydanticValidationError, json.JSONDecodeError):
        return JSONResponse(status_code=400, content={"detail": "Invalid webhook event envelope."})

    try:
        result = await use_case.execute(
            ReceiveWebhookEventInput(
                raw_payload=raw_payload,
                signature=signature,
                event=EventInput(
                    event_id=parsed.event_id,
                    event_type=parsed.event_type,
                    occurred_at=parsed.occurred_at,
                    data=parsed.data,
                ),
            )
        )
    except InvalidSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Invalid webhook signature."})
    except ValidationError:
        return JSONResponse(status_code=400, content={"detail": "Invalid webhook event envelope."})

    status_code = 200 if result.duplicate else 202
    return JSONResponse(
        status_code=status_code,
        content={
            "event_id": str(result.event_id),
            "status": result.status.value,
            "duplicate": result.duplicate,
        },
    )
