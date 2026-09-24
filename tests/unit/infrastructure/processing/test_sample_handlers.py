from tests.unit.application.support import build_event

from reliable_webhook_api.infrastructure.processing.sample_handlers import (
    handle_customer_created,
    handle_invoice_paid,
)


async def test_sample_handlers_accept_supported_events() -> None:
    event = build_event()

    await handle_customer_created(event)
    await handle_invoice_paid(event)
