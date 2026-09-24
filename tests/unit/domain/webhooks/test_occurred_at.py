from datetime import UTC, datetime

import pytest

from reliable_webhook_api.domain import OccurredAt


def test_occurred_at_accepts_timezone_aware_timestamp() -> None:
    timestamp = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    occurred_at = OccurredAt(timestamp)

    assert occurred_at.value == timestamp


def test_occurred_at_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="Occurred timestamp must be timezone-aware"):
        OccurredAt(datetime(2026, 9, 24, 12, 0))
