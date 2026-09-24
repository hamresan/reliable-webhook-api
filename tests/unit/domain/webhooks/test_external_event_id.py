import pytest

from reliable_webhook_api.domain import ExternalEventId


@pytest.mark.parametrize("value", ["", "   "])
def test_external_event_id_rejects_empty_value(value: str) -> None:
    with pytest.raises(ValueError, match="External event id"):
        ExternalEventId(value)
