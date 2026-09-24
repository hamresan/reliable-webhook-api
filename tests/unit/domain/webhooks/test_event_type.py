import pytest

from reliable_webhook_api.domain import EventType


@pytest.mark.parametrize("value", ["", "   "])
def test_event_type_rejects_empty_value(value: str) -> None:
    with pytest.raises(ValueError, match="Event type"):
        EventType(value)
