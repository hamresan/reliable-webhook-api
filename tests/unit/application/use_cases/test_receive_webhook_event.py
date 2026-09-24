from datetime import UTC, datetime
from uuid import UUID

import pytest
from tests.unit.application.use_cases.fakes import (
    FakeClock,
    FakeSignatureVerifier,
    FakeTransaction,
    InMemoryEventRepository,
)

from reliable_webhook_api.application.dto import EventInput, ReceiveWebhookEventInput
from reliable_webhook_api.application.errors import InvalidSignatureError, ValidationError
from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    ExternalEventId,
    ProviderName,
    ReceivedAt,
    WebhookEvent,
)

EVENT_ID = UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def make_request(
    *,
    signature: str | None = "signature",
    event_type: str = "invoice.paid",
    occurred_at: datetime = NOW,
    event: EventInput | None = None,
) -> ReceiveWebhookEventInput:
    return ReceiveWebhookEventInput(
        raw_payload=b'{"exact":"bytes"}',
        signature=signature,
        event=event
        or EventInput(
            event_id=EVENT_ID,
            event_type=event_type,
            occurred_at=occurred_at,
            data={"invoice_id": "inv_1"},
        ),
    )


def make_use_case(
    repository: InMemoryEventRepository,
    verifier: FakeSignatureVerifier,
) -> ReceiveWebhookEvent:
    return ReceiveWebhookEvent(
        repository=repository,
        signature_verifier=verifier,
        clock=FakeClock(NOW),
        transaction=FakeTransaction(),
    )


async def test_receives_new_event_after_signature_verification() -> None:
    repository = InMemoryEventRepository()
    verifier = FakeSignatureVerifier(True)
    use_case = make_use_case(repository, verifier)

    result = await use_case.execute(make_request())

    assert result.event_id == EVENT_ID
    assert result.status is EventStatus.RECEIVED
    assert not result.duplicate
    assert verifier.calls == [(b'{"exact":"bytes"}', "signature")]
    assert repository.add_calls == 1


async def test_returns_stable_duplicate_result_without_second_add() -> None:
    repository = InMemoryEventRepository()
    repository.events[EventId(EVENT_ID)] = WebhookEvent(
        id=EventId(EVENT_ID),
        provider=ProviderName("generic"),
        external_event_id=ExternalEventId(str(EVENT_ID)),
        event_type=EventType("invoice.paid"),
        payload={"data": {"invoice_id": "inv_1"}},
        status=EventStatus.RECEIVED,
        received_at=ReceivedAt(NOW),
    )
    verifier = FakeSignatureVerifier(True)
    use_case = make_use_case(repository, verifier)

    result = await use_case.execute(make_request())

    assert result.event_id == EVENT_ID
    assert result.status is EventStatus.RECEIVED
    assert result.duplicate
    assert repository.add_calls == 0


@pytest.mark.parametrize(
    "request",
    [
        make_request(event_type="   "),
        make_request(occurred_at=datetime(2026, 9, 24, 12, 0)),
        ReceiveWebhookEventInput(
            raw_payload=b"not-json",
            signature="signature",
            event=None,
        ),
    ],
)
async def test_rejects_invalid_envelope_after_signature_verification(
    request: ReceiveWebhookEventInput,
) -> None:
    repository = InMemoryEventRepository()
    verifier = FakeSignatureVerifier(True)
    use_case = make_use_case(repository, verifier)

    with pytest.raises(ValidationError, match="Invalid webhook event envelope"):
        await use_case.execute(request)

    assert verifier.calls
    assert repository.add_calls == 0


@pytest.mark.parametrize("signature", [None, "bad"])
async def test_signature_failure_creates_no_event(
    signature: str | None,
) -> None:
    repository = InMemoryEventRepository()
    verifier = FakeSignatureVerifier(signature != "bad")
    use_case = make_use_case(repository, verifier)

    with pytest.raises(InvalidSignatureError, match="Invalid webhook signature"):
        await use_case.execute(make_request(signature=signature))

    assert repository.events == {}
    assert repository.add_calls == 0
