from datetime import datetime

import pytest

from reliable_webhook_api.domain import ReceivedAt


def test_received_at_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ReceivedAt(datetime.now())
