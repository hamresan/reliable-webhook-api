from reliable_webhook_api.domain import EventStatus


def test_event_status_exposes_expected_values() -> None:
    assert {status.value for status in EventStatus} == {
        "received",
        "processing",
        "processed",
        "failed",
        "retry_scheduled",
        "dead_letter",
    }
