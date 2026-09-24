from reliable_webhook_api.application.processing import ProcessingFailureMapper


def test_maps_processor_exception_to_safe_failure_reason() -> None:
    failure = ProcessingFailureMapper().from_exception(RuntimeError("downstream rejected event"))

    assert failure.code.value == "processor_error"
    assert failure.message.value == "downstream rejected event"


def test_uses_fallback_for_empty_exception_message() -> None:
    failure = ProcessingFailureMapper().from_exception(RuntimeError())

    assert failure.code.value == "processor_error"
    assert failure.message.value == "Event processor failed."
