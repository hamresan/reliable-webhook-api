import pytest

from reliable_webhook_api.application.errors import (
    ApplicationError,
    ConflictError,
    DuplicateEventError,
    InvalidSignatureError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        NotFoundError,
        InvalidSignatureError,
        InvalidTransitionError,
        ValidationError,
        ConflictError,
        DuplicateEventError,
    ],
)
def test_application_errors_share_common_base(error_type: type[ApplicationError]) -> None:
    assert issubclass(error_type, ApplicationError)


def test_duplicate_event_is_a_conflict() -> None:
    assert issubclass(DuplicateEventError, ConflictError)
