from datetime import UTC, datetime, timedelta

import pytest

from reliable_webhook_api.domain import ProcessingAttempt


def test_processing_attempt_rejects_number_below_one() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        ProcessingAttempt(number=0, started_at=datetime.now(UTC))


def test_processing_attempt_rejects_naive_started_at() -> None:
    with pytest.raises(ValueError, match="started_at"):
        ProcessingAttempt(number=1, started_at=datetime.now())


def test_processing_attempt_rejects_naive_finished_at() -> None:
    with pytest.raises(ValueError, match="finished_at"):
        ProcessingAttempt(
            number=1,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(),
        )


def test_processing_attempt_rejects_finish_before_start() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValueError, match="before"):
        ProcessingAttempt(
            number=1,
            started_at=started_at,
            finished_at=started_at - timedelta(seconds=1),
        )
