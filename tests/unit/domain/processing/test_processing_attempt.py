from datetime import UTC, datetime, timedelta

import pytest

from reliable_webhook_api.domain import (
    AttemptNumber,
    ProcessingAttempt,
    ProcessingPeriod,
    ProcessingTimestamp,
)


def test_attempt_number_rejects_number_below_one() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        AttemptNumber(0)


def test_processing_timestamp_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ProcessingTimestamp(datetime.now())


def test_processing_period_rejects_finish_before_start() -> None:
    started_at = ProcessingTimestamp(datetime.now(UTC))
    finished_at = ProcessingTimestamp(started_at.value - timedelta(seconds=1))

    with pytest.raises(ValueError, match="before"):
        ProcessingPeriod(started_at=started_at, finished_at=finished_at)


def test_processing_attempt_composes_valid_domain_values() -> None:
    attempt = ProcessingAttempt(
        number=AttemptNumber(1),
        period=ProcessingPeriod(
            started_at=ProcessingTimestamp(datetime.now(UTC)),
        ),
    )

    assert attempt.number == AttemptNumber(1)
    assert attempt.period.finished_at is None
    assert attempt.failure_reason is None
