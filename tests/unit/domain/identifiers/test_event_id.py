from uuid import uuid4

from reliable_webhook_api.domain import EventId


def test_event_id_preserves_uuid_value() -> None:
    value = uuid4()

    event_id = EventId(value)

    assert event_id.value == value
