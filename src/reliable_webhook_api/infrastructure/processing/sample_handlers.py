import logging

from reliable_webhook_api.domain import WebhookEvent

logger = logging.getLogger(__name__)


async def handle_customer_created(event: WebhookEvent) -> None:
    logger.info("sample_event_processed event_id=%s event_type=%s", event.id.value, event.event_type.value)


async def handle_invoice_paid(event: WebhookEvent) -> None:
    logger.info("sample_event_processed event_id=%s event_type=%s", event.id.value, event.event_type.value)
